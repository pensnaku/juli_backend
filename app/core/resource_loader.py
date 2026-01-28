"""Resource loader utility for loading configuration files"""
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml


class ResourceLoader:
    """Simple utility for loading resource files (YAML, JSON, etc.)"""

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize resource loader

        Args:
            base_path: Base directory for resources. Defaults to project root/resources
        """
        if base_path is None:
            # Get project root (3 levels up from this file: core -> app -> project_root)
            project_root = Path(__file__).parent.parent.parent
            base_path = project_root / "resources"

        self.base_path = Path(base_path)

    def load_yaml(self, relative_path: str) -> Dict[str, Any]:
        """
        Load a YAML file from the resources directory

        Args:
            relative_path: Path relative to resources directory (e.g., "questionnaires/onboarding.yml")

        Returns:
            Parsed YAML content as dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is malformed
        """
        file_path = self.base_path / relative_path

        if not file_path.exists():
            raise FileNotFoundError(f"Resource file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)

    def load_questionnaire(self, questionnaire_name: str) -> Dict[str, Any]:
        """
        Load a questionnaire by name

        Args:
            questionnaire_name: Name of questionnaire file (without .yml extension)

        Returns:
            Questionnaire configuration as dictionary

        Example:
            loader = ResourceLoader()
            questionnaire = loader.load_questionnaire("onboarding_questionnaire")
        """
        return self.load_yaml(f"questionnaires/{questionnaire_name}.yml")

    def load_daily_questionnaire(self, condition_filename: str) -> Dict[str, Any]:
        """
        Load a daily questionnaire by condition filename

        Args:
            condition_filename: Condition-specific filename (e.g., 'asthma', 'diabetes')

        Returns:
            Questionnaire configuration as dictionary

        Raises:
            FileNotFoundError: If questionnaire file doesn't exist

        Example:
            loader = ResourceLoader()
            questionnaire = loader.load_daily_questionnaire("asthma")
        """
        # Try both .yml and .yaml extensions
        for ext in ['.yml', '.yaml']:
            file_path = self.base_path / f"questionnaires/daily/{condition_filename}{ext}"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as file:
                    return yaml.safe_load(file)

        raise FileNotFoundError(
            f"Daily questionnaire not found: {condition_filename}"
        )

    def list_daily_questionnaires(self) -> List[str]:
        """
        List all available daily questionnaire filenames (without extension)

        Returns:
            List of condition filenames (e.g., ['asthma', 'diabetes', 'migraine'])
        """
        daily_path = self.base_path / "questionnaires" / "daily"
        if not daily_path.exists():
            return []

        return [
            f.stem for f in daily_path.iterdir()
            if f.suffix in ['.yml', '.yaml'] and f.is_file()
        ]

    def load_condition_assessment(self, questionnaire_key: str) -> Dict[str, Any]:
        """
        Load a condition assessment questionnaire by key

        Args:
            questionnaire_key: Questionnaire key (e.g., 'depression', 'chronic_pain')

        Returns:
            Questionnaire configuration as dictionary

        Raises:
            FileNotFoundError: If questionnaire file doesn't exist

        Example:
            loader = ResourceLoader()
            questionnaire = loader.load_condition_assessment("depression")
        """
        # Try both .yml and .yaml extensions
        for ext in ['.yml', '.yaml']:
            file_path = self.base_path / f"questionnaires/condition-assessment/{questionnaire_key}{ext}"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as file:
                    return yaml.safe_load(file)

        raise FileNotFoundError(
            f"Condition assessment questionnaire not found: {questionnaire_key}"
        )

    def list_condition_assessments(self) -> List[str]:
        """
        List all available condition assessment questionnaire filenames (without extension)

        Returns:
            List of questionnaire keys (e.g., ['depression', 'anxiety', 'asthma'])
        """
        assessment_path = self.base_path / "questionnaires" / "condition-assessment"
        if not assessment_path.exists():
            return []

        return [
            f.stem for f in assessment_path.iterdir()
            if f.suffix in ['.yml', '.yaml'] and f.is_file()
        ]

    def get_resource_path(self, relative_path: str) -> Path:
        """
        Get absolute path to a resource file

        Args:
            relative_path: Path relative to resources directory

        Returns:
            Absolute path to resource file
        """
        return self.base_path / relative_path


# Singleton instance for convenience
_default_loader: Optional[ResourceLoader] = None


def get_resource_loader() -> ResourceLoader:
    """
    Get the default ResourceLoader instance

    Returns:
        Default ResourceLoader instance
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = ResourceLoader()
    return _default_loader