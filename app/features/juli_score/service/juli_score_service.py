"""Main Juli Score service"""
import logging
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session

from app.features.juli_score.constants import (
    CONDITION_FACTORS,
    MIN_DATA_POINTS,
    get_condition_name,
)
from app.features.juli_score.domain.entities import JuliScore
from app.features.juli_score.domain.schemas import (
    JuliScoreResponse,
    JuliScoreListResponse,
    JuliScoreLatestResponse,
    FactorBreakdown,
)
from app.features.juli_score.repository import JuliScoreRepository
from app.features.juli_score.service.factor_calculators import calculate_factors_for_condition

logger = logging.getLogger(__name__)


class JuliScoreService:
    """Service for calculating and managing Juli Scores"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = JuliScoreRepository(db)

    def calculate_and_save_score(
        self,
        user_id: int,
        condition_code: str,
        target_date: Optional[date] = None,
    ) -> Optional[JuliScore]:
        """
        Calculate and save Juli Score if different from last score.

        Returns:
            JuliScore if calculated, None if insufficient data
        """
        if target_date is None:
            target_date = date.today()

        # Get factor configs for this condition
        factors_config = CONDITION_FACTORS.get(condition_code)
        if not factors_config:
            logger.warning(f"Unsupported condition: {condition_code}")
            return None

        # Calculate all factors
        factor_results = calculate_factors_for_condition(
            self.repo, user_id, condition_code, factors_config, target_date
        )

        # Count data points and calculate totals
        # Only count weights for factors that have data (per Juli Score spec)
        total_score = 0.0
        total_weight = 0
        data_points = 0
        factor_data = {}

        for factor_name, (score, raw_input) in factor_results.items():
            config = factors_config[factor_name]

            if score is not None:
                total_score += score
                total_weight += config.weight  # Only add weight when we have data
                data_points += 1

            factor_data[factor_name] = {
                "score": score,
                "input": raw_input,
            }

        # Check minimum data points
        if data_points < MIN_DATA_POINTS:
            logger.info(
                f"Insufficient data for user {user_id}, condition {condition_code}: "
                f"{data_points}/{MIN_DATA_POINTS}"
            )
            return None

        # Calculate final score
        final_score = round((total_score / total_weight) * 100)
        final_score = max(0, min(100, final_score))

        # Check if score is different from last
        last_score = self.repo.get_latest_juli_score(user_id, condition_code)
        if last_score and last_score.score == final_score:
            # Score unchanged, don't save duplicate
            logger.debug(
                f"Score unchanged for user {user_id}, condition {condition_code}: {final_score}"
            )
            return last_score

        # Create new JuliScore entity
        effective_at = datetime.combine(target_date, datetime.now().time())
        juli_score = JuliScore(
            user_id=user_id,
            condition_code=condition_code,
            score=final_score,
            effective_at=effective_at,
            data_points_used=data_points,
            total_weight=total_weight,
            # Factor inputs and scores
            air_quality_input=self._to_decimal(factor_data.get("air_quality", {}).get("input")),
            air_quality_score=self._to_decimal(factor_data.get("air_quality", {}).get("score")),
            sleep_input=self._to_decimal(factor_data.get("sleep", {}).get("input")),
            sleep_score=self._to_decimal(factor_data.get("sleep", {}).get("score")),
            biweekly_input=self._to_decimal(factor_data.get("biweekly", {}).get("input")),
            biweekly_score=self._to_decimal(factor_data.get("biweekly", {}).get("score")),
            active_energy_input=self._to_decimal(factor_data.get("active_energy", {}).get("input")),
            active_energy_score=self._to_decimal(factor_data.get("active_energy", {}).get("score")),
            medication_input=self._to_decimal(factor_data.get("medication", {}).get("input")),
            medication_score=self._to_decimal(factor_data.get("medication", {}).get("score")),
            mood_input=self._to_decimal(factor_data.get("mood", {}).get("input")),
            mood_score=self._to_decimal(factor_data.get("mood", {}).get("score")),
            hrv_input=self._to_decimal(factor_data.get("hrv", {}).get("input")),
            hrv_score=self._to_decimal(factor_data.get("hrv", {}).get("score")),
            pollen_input=self._to_decimal(factor_data.get("pollen", {}).get("input")),
            pollen_score=self._to_decimal(factor_data.get("pollen", {}).get("score")),
            inhaler_input=self._to_decimal(factor_data.get("inhaler", {}).get("input")),
            inhaler_score=self._to_decimal(factor_data.get("inhaler", {}).get("score")),
        )

        self.repo.save_juli_score(juli_score)
        self.db.commit()

        logger.info(
            f"Saved new Juli Score for user {user_id}, condition {condition_code}: {final_score}"
        )
        return juli_score

    def get_latest_score(
        self,
        user_id: int,
        condition_code: str,
    ) -> Optional[JuliScoreResponse]:
        """Get the most recent score for a condition"""
        score = self.repo.get_latest_juli_score(user_id, condition_code)
        if not score:
            return None
        return self._entity_to_response(score)

    def get_latest_scores_for_user(
        self,
        user_id: int,
    ) -> JuliScoreLatestResponse:
        """Get latest scores for all user conditions"""
        condition_codes = self.repo.get_user_conditions(user_id)

        scores = []
        conditions_without_score = []

        for condition_code in condition_codes:
            score = self.repo.get_latest_juli_score(user_id, condition_code)
            if score:
                scores.append(self._entity_to_response(score))
            else:
                conditions_without_score.append(condition_code)

        return JuliScoreLatestResponse(
            scores=scores,
            conditions_without_score=conditions_without_score,
        )

    def get_score_history(
        self,
        user_id: int,
        condition_code: str,
        page: int = 1,
        page_size: int = 20,
    ) -> JuliScoreListResponse:
        """Get paginated score history for a condition"""
        scores, total = self.repo.get_juli_score_history(
            user_id, condition_code, page, page_size
        )

        return JuliScoreListResponse(
            scores=[self._entity_to_response(s) for s in scores],
            total=total,
            page=page,
            page_size=page_size,
        )

    def _entity_to_response(self, entity: JuliScore) -> JuliScoreResponse:
        """Convert JuliScore entity to response schema"""
        factors_config = CONDITION_FACTORS.get(entity.condition_code, {})

        factors = []
        for factor_name, config in factors_config.items():
            input_attr = f"{factor_name}_input"
            score_attr = f"{factor_name}_score"

            input_value = getattr(entity, input_attr, None)
            score_value = getattr(entity, score_attr, None)

            factors.append(FactorBreakdown(
                name=factor_name,
                input_value=input_value,
                score=score_value,
                weight=config.weight,
                available=score_value is not None,
            ))

        return JuliScoreResponse(
            id=entity.id,
            condition_code=entity.condition_code,
            condition_name=get_condition_name(entity.condition_code),
            score=entity.score,
            effective_at=entity.effective_at,
            factors=factors,
            data_points_used=entity.data_points_used,
            total_weight=entity.total_weight,
            created_at=entity.created_at,
        )

    @staticmethod
    def _to_decimal(value) -> Optional[Decimal]:
        """Convert value to Decimal if not None"""
        if value is None:
            return None
        return Decimal(str(value))
