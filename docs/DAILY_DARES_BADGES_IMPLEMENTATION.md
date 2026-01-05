# Daily Dares Badges Implementation Guide

This document provides a comprehensive guide for implementing the Daily Dares badges system. It covers the database models, badge types, criteria evaluation, consumer/worker implementation, and API endpoints.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Flow](#architecture-flow)
3. [Database Models](#database-models)
4. [Badge Types and Definitions](#badge-types-and-definitions)
5. [Badge Evaluation Logic](#badge-evaluation-logic)
6. [Consumer/Worker Implementation](#consumerworker-implementation)
7. [Repository Methods](#repository-methods)
8. [API Endpoints](#api-endpoints)
9. [Pub/Sub Messaging](#pubsub-messaging)
10. [Migration/Seeding Badges](#migrationseeding-badges)
11. [Implementation Checklist](#implementation-checklist)

---

## Overview

The badges system awards users achievements based on their Daily Dares completion patterns. There are two main categories:

- **Regular Badges**: Progression-based badges earned through streaks, points, and consistency
- **Monthly Badges**: Time-limited badges with category-specific criteria for each month

Badges are evaluated asynchronously via a Pub/Sub consumer whenever a user completes a daily dare (marks a UserTarget as achieved).

---

## Architecture Flow

```
User completes Daily Dare (marks target as achieved)
    │
    ▼
UserTarget.save() triggers post-save hook
    │
    ▼
publishMessage(TOPICS.BADGES, userTargetData)
    │
    ▼
Google Cloud Pub/Sub Topic receives message
    │
    ▼
badgesConsumer() subscription listener processes message
    │
    ▼
processMessageFromSubscription() parses UserTarget data
    │
    ▼
For each badge type, calls corresponding helper method:
  ├── assignCenturyBadge()
  ├── assignDaredevilBadge(levels 1-5)
  ├── assignDecadeBadge()
  ├── assignMilleniumBadge()
  ├── assignStreakBadge(levels 1-5)
  ├── assignStrongStartBadge(levels 1-4)
  └── assignMonthlyBadge()
    │
    ▼
Each helper method:
  ├── Fetches badge by slug from database
  ├── Calculates criteria using aggregation queries
  └── If criteria met → assignBadgeToUser()
    │
    ▼
UserBadgesRepository.assignBadgeToUser():
  ├── Check if already earned (respecting canBeMultiple)
  └── Create UserBadge document if eligible
    │
    ▼
Badge awarded to user
```

---

## Database Models

### Badge Model

Stores badge definitions (regular and monthly).

```typescript
interface Badge {
    name: string;              // Badge display name (required)
    description: string;       // Badge description
    slug: string;              // Unique URL-friendly identifier (required, unique)
    preText: string;           // Text shown before earning
    postText: string;          // Text shown after earning
    canBeMultiple: boolean;    // Can be earned multiple times (default: false)
    priority: number;          // Display order for regular badges
    level: number;             // Difficulty/tier level (1-5)
    type: 'regular' | 'monthly';  // Badge classification
    month: number;             // For monthly badges (1-12)
    year: number;              // For monthly badges
    image: {
        small: {
            earned: { image?: string; file?: string; url?: string; };
            notEarned: { image?: string; file?: string; url?: string; };
        };
        large: {
            earned: { image?: string; file?: string; url?: string; };
            notEarned: { image?: string; file?: string; url?: string; };
        };
    };
    criteria?: {
        category?: string;         // Target category (e.g., 'nutrition', 'sleep')
        byPoints: boolean;         // Points-based criteria
        expectedCount: number;     // Count requirement
        expectedPointSum: number;  // Points total requirement
        uniqueDayCount?: number;   // Unique days requirement
    };
    createdAt?: Date;
    updatedAt?: Date;
}
```

**Schema Definition (Mongoose):**

```typescript
const BadgesSchema = new Schema(
    {
        name: { type: String, required: true },
        description: { type: String, required: false },
        slug: { type: String, required: true, unique: true },
        canBeMultiple: { type: Boolean, default: false },
        priority: { type: Number },
        level: { type: Number },
        preText: { type: String, required: false },
        postText: { type: String, required: false },
        month: { type: Number },
        type: {
            type: String,
            enum: ['monthly', 'regular'],
            default: 'regular',
        },
        year: { type: Number },
        image: {
            small: {
                earned: {
                    image: { type: String },
                    file: { type: String },
                    url: { type: String },
                },
                notEarned: {
                    image: { type: String },
                    file: { type: String },
                    url: { type: String },
                },
            },
            large: {
                earned: {
                    image: { type: String },
                    file: { type: String },
                    url: { type: String },
                },
                notEarned: {
                    image: { type: String },
                    file: { type: String },
                    url: { type: String },
                },
            },
        },
        criteria: {
            category: { type: String },
            byPoints: { type: Boolean },
            expectedCount: { type: Number, default: 0 },
            expectedPointSum: { type: Number, default: 0 },
            uniqueDayCount: { type: Number },
        },
    },
    { timestamps: true },
);
```

### UserBadge Model

Tracks which badges users have earned.

```typescript
interface UserBadge {
    badge: ObjectId;       // Reference to Badge
    userID: string;        // User identifier (required, indexed)
    createdAt?: Date;      // When badge was earned (indexed)
    updatedAt?: Date;
}
```

**Schema Definition (Mongoose):**

```typescript
const UserBadgesSchema = new Schema(
    {
        badge: { type: Types.ObjectId, ref: 'Badge' },
        userID: { type: String, required: true },
    },
    { timestamps: true },
);
```

### UserTarget Model (Trigger Point)

The post-save hook on UserTarget triggers badge evaluation.

```typescript
interface UserTarget {
    userID: string;
    points: number;
    assignedDate: Date;
    achieved: boolean;
    status: 'open' | 'close';
    target: {
        target: string;
        category: string;
        subcategory: string;
        condition: string;
        points: number;
    };
    isRecommendation: boolean;
    createdAt?: Date;
    updatedAt?: Date;
}

// Critical: Post-save hook that triggers badge evaluation
UserTargetSchema.post('save', function (doc) {
    if (!this.isNew && doc.achieved) {
        publishMessage(TOPICS.BADGES, JSON.stringify(doc));
    }
});
```

---

## Badge Types and Definitions

### Constants

```typescript
const BADGE_TYPES = {
    MONTHLY: 'monthly',
    REGULAR: 'regular',
};

const BADGE_SLUGS = {
    DAREDEVIL: 'daredevil',
    DECADE: 'decade',
    CENTURY: 'century',
    MILLENIUM: 'millenium',
    SUPER_WILLPOWER: 'super-willpower',
    STREAK: 'streak',
    STRONG_START: 'strong-start',
    THE_WARRIOR: 'the-warrior',
};
```

### Regular Badges

| Badge Name | Slug | Levels | Criteria | canBeMultiple | Priority |
|------------|------|--------|----------|---------------|----------|
| **Strong Start** | `strong-start1` to `strong-start4` | 1-4 | 2, 5, 10, 15 consecutive active days (any dare completed) | Yes | 1, 4, 5, 6 |
| **Daredevil** | `daredevil1` to `daredevil5` | 1-5 | 1, 7, 14, 30, 60 consecutive days with ALL 4 dares completed | Yes | 2, 10, 12, 13, 17 |
| **Streak** | `streak1` to `streak5` | 1-5 | 20, 50, 100, 180, 365 consecutive active days | Yes | 7, 9, 11, 14, 16 |
| **Decade** | `decade` | - | Earn 10 total points | No | 3 |
| **Century** | `century` | - | Earn 100 total points | No | 8 |
| **Millenium** | `millenium` | - | Earn 1000 total points | Yes | 15 |
| **The Warrior** | `the-warrior` | - | Awarded on first app access | No | - |

### Monthly Badges

Monthly badges are time-limited and have category-specific criteria:

| Example Badge | Month/Year | Criteria |
|---------------|------------|----------|
| The Dares Challenge | June 2021 | Complete 50 dares (any category) |
| Sleep Month | July 2021 | Complete 10 Sleep category dares |
| Wellness Month | August 2021 | Complete 10 Wellness category dares |
| Nutrition Month | March 2022 | Complete 10 Nutrition category dares |

---

## Badge Evaluation Logic

### Core Processing Function

```typescript
async function processBadgeByDay({
    allDaresCompleted,   // Must complete ALL 4 dares per day
    userID,
    mustBeConsecutive,   // Days must be sequential
    startDate,
    endDate,
    numberOfDays,        // Target duration
    badge,
}): Promise<void> {
    // 1. Aggregate completed targets grouped by day
    const data = await UserTargetRepository.aggregateOpenTargetsByDay({
        userID,
        startDate,
        endDate,
    });

    let badgeEarned = false;
    let successDayCount = 0;

    // 2. Verify we have the expected number of days
    if (numberOfDays === data.length) {
        for (let x = 0; x < data.length; x++) {
            const current = data[x];
            let previous;
            if (x > 0) {
                previous = data[x - 1];
            }

            // 3. Check consecutive days (if required)
            if (previous && mustBeConsecutive && previous._id - current._id !== 1) {
                break;  // Not consecutive, stop evaluation
            }

            // 4. Filter to achieved targets only
            const filteredTargets = current.data.filter((target) => target.achieved);

            // 5. Check if all dares completed (if required)
            if (allDaresCompleted && filteredTargets.length !== 4) {
                break;  // Didn't complete all 4 dares
            } else if (allDaresCompleted && filteredTargets.length === 4) {
                successDayCount++;
            }

            // 6. At least one dare must be completed
            if (filteredTargets.length < 1) {
                badgeEarned = false;
                break;
            }
            badgeEarned = true;
        }

        if (successDayCount === numberOfDays) {
            badgeEarned = true;
        }
    }

    // 7. Award badge if criteria met
    if (badgeEarned) {
        UserBadgesHelper.assignBadgeToUser({ userID, badge });
    }
}
```

### Badge Assignment Logic

```typescript
async function assignBadgeToUser({
    userID,
    badge,
    canBeMultiple = false,
}): Promise<UserBadge | void> {
    const query = { userID, badge: badge._id };

    // Find the most recent assignment of this badge
    const assignedBadge = await UserBadge.findOne(query).sort({ createdAt: -1 });

    // Check duplicate prevention rules
    if (assignedBadge) {
        // Badge already earned and cannot be earned multiple times
        if (!canBeMultiple) return;

        // Badge can be multiple but was already earned today
        if (moment(assignedBadge.createdAt).isSame(moment(new Date()), 'day')) {
            return;
        }
    }

    // Create new badge entry
    return UserBadge.create(query);
}
```

### Specific Badge Helper Methods

#### Daredevil Badge (All Dares Completed)

```typescript
async function assignDaredevilBadge({ userID, level }): Promise<void> {
    const slug = `daredevil${level}`;
    const badge = await BadgesRepository.getBadgeBySlug({ slug });

    const dayRequirements = {
        1: 1,   // 1 day
        2: 7,   // 1 week
        3: 14,  // 2 weeks
        4: 30,  // 1 month
        5: 60,  // 2 months
    };
    const numberOfDays = dayRequirements[level];

    const todaysDate = moment();

    processBadgeByDay({
        allDaresCompleted: true,    // Must complete ALL 4 dares
        mustBeConsecutive: true,
        startDate: startOfDay(subDays(todaysDate.toDate(), numberOfDays - 1)),
        endDate: todaysDate.endOf('day').toDate(),
        numberOfDays,
        userID,
        badge,
    });
}
```

#### Strong Start Badge (Any Dare Completed)

```typescript
async function assignStrongStartBadge({ userID, level }): Promise<void> {
    const slug = `strong-start${level}`;
    const badge = await BadgesRepository.getBadgeBySlug({ slug });

    const dayRequirements = {
        1: 2,   // 2 days
        2: 5,   // 5 days
        3: 10,  // 10 days
        4: 15,  // 15 days
    };
    const numberOfDays = dayRequirements[level];

    const todaysDate = moment();

    processBadgeByDay({
        allDaresCompleted: false,   // Any dare counts
        mustBeConsecutive: true,
        startDate: startOfDay(subDays(todaysDate.toDate(), numberOfDays - 1)),
        endDate: todaysDate.endOf('day').toDate(),
        numberOfDays,
        userID,
        badge,
    });
}
```

#### Streak Badge

```typescript
async function assignStreakBadge({ userID, level }): Promise<void> {
    const slug = `streak${level}`;
    const badge = await BadgesRepository.getBadgeBySlug({ slug });

    const dayRequirements = {
        1: 20,   // 20 days
        2: 50,   // 50 days
        3: 100,  // 100 days
        4: 180,  // 6 months
        5: 365,  // 1 year
    };
    const numberOfDays = dayRequirements[level];

    const todaysDate = moment();

    processBadgeByDay({
        allDaresCompleted: false,
        mustBeConsecutive: true,
        startDate: startOfDay(subDays(todaysDate.toDate(), numberOfDays - 1)),
        endDate: todaysDate.endOf('day').toDate(),
        numberOfDays,
        userID,
        badge,
    });
}
```

#### Points-Based Badges (Decade, Century, Millenium)

```typescript
async function assignDecadeBadge({ userID }): Promise<void> {
    const badge = await BadgesRepository.getBadgeBySlug({ slug: 'decade' });

    // Get all-time point sum (no date range)
    const pointData = await UserTargetRepository.getPointSumOverTime({
        userID,
        achieved: true,
    });

    if (pointData.length) {
        const [{ pointSum }] = pointData;
        if (pointSum >= 10) {
            assignBadgeToUser({ userID, badge });
        }
    }
}

async function assignCenturyBadge({ userID }): Promise<void> {
    const badge = await BadgesRepository.getBadgeBySlug({ slug: 'century' });

    const pointData = await UserTargetRepository.getPointSumOverTime({
        userID,
        achieved: true,
    });

    if (pointData.length) {
        const [{ pointSum }] = pointData;
        if (pointSum >= 100) {
            assignBadgeToUser({ userID, badge });
        }
    }
}

async function assignMilleniumBadge({ userID }): Promise<void> {
    const badge = await BadgesRepository.getBadgeBySlug({ slug: 'millenium' });

    const pointData = await UserTargetRepository.getPointSumOverTime({
        userID,
        achieved: true,
    });

    if (pointData.length) {
        const [{ pointSum }] = pointData;
        if (pointSum >= 1000) {
            assignBadgeToUser({ userID, badge });
        }
    }
}
```

#### Monthly Badge

```typescript
async function assignMonthlyBadge({ userID, referenceDate }): Promise<void> {
    // Get month and year from reference date
    const month = referenceDate.month();
    const year = referenceDate.year();

    // Find the monthly badge for this month/year
    const monthlyBadge = await BadgesRepository.getBadgeByMonthAndYear({
        month: month + 1,  // moment months are 0-indexed
        year,
    });

    if (monthlyBadge) {
        // Get point/count data for the month
        const data = await UserTargetRepository.getPointSumOverTime({
            startDate: referenceDate.startOf('month').toDate(),
            endDate: referenceDate.endOf('month').toDate(),
            userID,
            achieved: true,
            category: monthlyBadge.criteria.category,
            uniqueDayCount: monthlyBadge.criteria.uniqueDayCount,
        });

        const [pointData] = data;
        const pointSum = pointData?.pointSum;
        const count = pointData?.count;

        // Check if any criteria is met
        const pointsGoalAchieved =
            monthlyBadge.criteria.expectedPointSum &&
            pointSum >= monthlyBadge.criteria.expectedPointSum;

        const countGoalAchieved =
            monthlyBadge.criteria.expectedCount &&
            count >= monthlyBadge.criteria.expectedCount;

        const dayCountGoalAchieved =
            monthlyBadge.criteria.uniqueDayCount &&
            monthlyBadge.criteria.uniqueDayCount <= data.length;

        if (pointsGoalAchieved || countGoalAchieved || dayCountGoalAchieved) {
            assignBadgeToUser({ userID, badge: monthlyBadge });
        }
    }
}
```

#### The Warrior Badge (First App Access)

```typescript
async function assignTheWarriorBadge({ userID }): Promise<void> {
    const badge = await BadgesRepository.getBadgeBySlug({
        slug: 'the-warrior',
    });
    assignBadgeToUser({ userID, badge });
}
```

**Note:** This is called when user first accesses the app/gets daily targets, not from the Pub/Sub consumer.

---

## Consumer/Worker Implementation

### Consumer Entry Point

```typescript
import { getPubSubClient } from '../core/messaging';
import { PUB_SUB_SUBSCRIPTION } from '../config/env';

export async function badgesConsumer() {
    const subscription = getPubSubClient().subscription(PUB_SUB_SUBSCRIPTION);

    const messageHandler = (message) => {
        processMessageFromSubscription(message);
        message.ack();  // Acknowledge receipt
    };

    subscription.on('message', messageHandler);
}
```

### Message Processing

```typescript
async function processMessageFromSubscription(message) {
    try {
        if (message != null) {
            const data: UserTargetInterface = JSON.parse(message.data);

            /**
             * The following are asynchronous calls that handle errors independently.
             * Failure of one does not break the flow of code.
             *
             * These are fire-and-forget calls - each checks eligibility and assigns
             * the badge if criteria are met.
             */

            // Points-based badges
            UserBadgesHelper.assignCenturyBadge({ userID: data.userID });
            UserBadgesHelper.assignDecadeBadge({ userID: data.userID });
            UserBadgesHelper.assignMilleniumBadge({ userID: data.userID });

            // Daredevil badges (all 5 levels)
            UserBadgesHelper.assignDaredevilBadge({ userID: data.userID, level: 1 });
            UserBadgesHelper.assignDaredevilBadge({ userID: data.userID, level: 2 });
            UserBadgesHelper.assignDaredevilBadge({ userID: data.userID, level: 3 });
            UserBadgesHelper.assignDaredevilBadge({ userID: data.userID, level: 4 });
            UserBadgesHelper.assignDaredevilBadge({ userID: data.userID, level: 5 });

            // Streak badges (all 5 levels)
            UserBadgesHelper.assignStreakBadge({ userID: data.userID, level: 1 });
            UserBadgesHelper.assignStreakBadge({ userID: data.userID, level: 2 });
            UserBadgesHelper.assignStreakBadge({ userID: data.userID, level: 3 });
            UserBadgesHelper.assignStreakBadge({ userID: data.userID, level: 4 });
            UserBadgesHelper.assignStreakBadge({ userID: data.userID, level: 5 });

            // Strong Start badges (all 4 levels)
            UserBadgesHelper.assignStrongStartBadge({ userID: data.userID, level: 1 });
            UserBadgesHelper.assignStrongStartBadge({ userID: data.userID, level: 2 });
            UserBadgesHelper.assignStrongStartBadge({ userID: data.userID, level: 3 });
            UserBadgesHelper.assignStrongStartBadge({ userID: data.userID, level: 4 });

            // Monthly badge (based on assigned date)
            UserBadgesHelper.assignMonthlyBadge({
                userID: data.userID,
                referenceDate: moment(data.assignedDate),
            });
        }
    } catch (err) {
        console.error(err);
    }
}
```

---

## Repository Methods

### BadgesRepository

```typescript
class BadgesRepository {
    // Get badge by unique slug
    static async getBadgeBySlug({ slug }): Promise<Badge> {
        return Badge.findOne({ slug }).lean();
    }

    // Get badge by month and year (for monthly badges)
    static async getBadgeByMonthAndYear({ month, year }): Promise<Badge> {
        return Badge.findOne({ month, year }).lean();
    }

    // Get badge by priority (for determining next badge)
    static async getBadgeByPriority({ priority }): Promise<Badge> {
        return Badge.findOne({ priority }).lean();
    }

    // Get monthly badge for current/future month
    static async getMonthlyBadge({ month, year, exclude }): Promise<Badge> {
        return Badge.findOne({
            _id: { $nin: exclude },
            month: { $gte: month },
            year: { $gte: year },
            type: 'monthly',
        }).lean();
    }

    // Get all badges, optionally filtered by type
    static async getBadges({ type }): Promise<Badge[]> {
        const condition = type ? { type } : {};
        return Badge.find(condition).lean();
    }
}
```

### UserBadgesRepository

```typescript
class UserBadgesRepository {
    // Assign badge to user (respects canBeMultiple flag)
    static async assignBadgeToUser({ userID, badge, canBeMultiple = false }): Promise<UserBadge | void> {
        const query = { userID, badge };
        const assignedBadge = await UserBadge.findOne(query).sort({ createdAt: -1 });

        if (assignedBadge && (!canBeMultiple || moment(assignedBadge.createdAt).isSame(moment(), 'day'))) {
            return;  // Badge already earned and cannot be re-earned
        }

        return UserBadge.create(query);
    }

    // Get all user badges, optionally filtered
    static async getUserBadges({ badge, userID, type }): Promise<UserBadge[]> {
        const condition: any = { userID };

        if (badge) condition.badge = badge;

        if (type) {
            const distinctIDs = await Badge.distinct('_id', { type });
            condition.badge = { $in: distinctIDs };
        }

        return UserBadge.find(condition).populate('badge').lean();
    }

    // Get next attainable badge based on type and last badge earned
    static async getNextAttainableBadge({ lastBadge, type, userID }): Promise<Badge> {
        let nextBadge = null;

        if (type === 'regular') {
            let currentPriority = lastBadge?.priority || 0;
            let hasAchieved = false;

            do {
                nextBadge = await BadgesRepository.getBadgeByPriority({
                    priority: ++currentPriority,
                });
                if (nextBadge) {
                    hasAchieved = await UserBadgesRepository.hasUserAchievedBadge({
                        userID,
                        badgeID: nextBadge._id,
                    });
                }
            } while (nextBadge !== null && hasAchieved !== false);

        } else if (type === 'monthly') {
            const date = new Date();
            const monthOfYear = date.getMonth() + 1;
            const year = date.getFullYear();

            nextBadge = await BadgesRepository.getMonthlyBadge({
                month: monthOfYear,
                year,
                exclude: lastBadge ? [lastBadge._id] : [],
            });
        }

        return nextBadge;
    }

    // Check if user has earned specific badge
    static async hasUserAchievedBadge({ badgeID, userID }): Promise<boolean> {
        const count = await UserBadge.countDocuments({ userID, badge: badgeID });
        return count > 0;
    }

    // Get all instances of a badge being earned
    static async getBadgeData({ badgeID }): Promise<any[]> {
        return UserBadge.find({ badge: badgeID }).populate('badge').lean();
    }
}
```

### UserTargetRepository (Badge-Related Methods)

```typescript
class UserTargetRepository {
    // Groups targets by day for consecutive day evaluation
    static async aggregateOpenTargetsByDay({ userID, startDate, endDate }): Promise<any[]> {
        return UserTarget.aggregate([
            {
                $match: {
                    userID,
                    status: 'open',
                    assignedDate: { $gte: startDate, $lt: endDate },
                },
            },
            {
                // Calculate a unique day identifier
                $addFields: {
                    dayOfYear: { $dayOfYear: '$assignedDate' },
                    year: { $year: '$assignedDate' },
                },
            },
            {
                // Combine to create unique day+year identifier
                $addFields: {
                    dayPlusYear: { $sum: ['$dayOfYear', '$year'] },
                },
            },
            {
                // Group all targets by day
                $group: {
                    _id: '$dayPlusYear',
                    data: { $push: '$$ROOT' },
                },
            },
            {
                // Sort chronologically
                $sort: { _id: 1 },
            },
        ]).allowDiskUse(true);
    }

    // Get point sums for badge evaluation
    static async getPointSumOverTime({
        startDate,
        endDate,
        achieved = true,
        userID,
        category,
        uniqueDayCount,
    }): Promise<any[]> {
        const matchClause: any = { achieved, userID };

        if (startDate || endDate) {
            matchClause.assignedDate = {};
            if (startDate) matchClause.assignedDate.$gte = startDate;
            if (endDate) matchClause.assignedDate.$lte = endDate;
        }

        if (category) {
            // Capitalize first letter to match stored format
            matchClause['target.category'] = category.charAt(0).toUpperCase() + category.slice(1);
        }

        return UserTarget.aggregate([
            { $match: matchClause },
            {
                $group: {
                    // Group by day if counting unique days, otherwise aggregate all
                    _id: uniqueDayCount ? '$assignedDate' : null,
                    count: { $sum: 1 },
                    pointSum: { $sum: '$points' },
                },
            },
        ]);
    }
}
```

---

## API Endpoints

### Routes

```
GET /v1/badges                      - Get all user badges
GET /v1/badges/dashboard/overview   - Get last and next badges
GET /v1/badges/dashboard/data       - Get all badges with achievement status
GET /v1/badges/:badgeID             - Get detailed badge data
```

### Service Methods

```typescript
class UserBadgesService {
    // Get all user badges
    static async getUserBadges(req, res) {
        const { userID } = req.query;
        const userBadges = await UserBadgesRepository.getUserBadges({ userID });
        return res.json({ success: true, data: userBadges });
    }

    // Dashboard overview: last earned and next attainable badges
    static async getBadgesDashboardOverview(req, res) {
        const { userID } = req.query;
        const userBadges = await UserBadgesRepository.getUserBadges({ userID });

        // Find last regular badge earned
        const regularBadges = userBadges.filter(b => b.badge?.type === 'regular');
        const lastAttainedRegularBadge = regularBadges[regularBadges.length - 1];

        // Get next regular badge
        const nextRegularBadge = await UserBadgesRepository.getNextAttainableBadge({
            lastBadge: lastAttainedRegularBadge,
            type: 'regular',
            userID,
        });

        // Get next monthly badge
        const monthlyBadges = userBadges.filter(b => b.badge?.type === 'monthly');
        const lastMonthlyBadge = monthlyBadges[monthlyBadges.length - 1];
        const nextMonthlyBadge = await UserBadgesRepository.getNextAttainableBadge({
            lastBadge: lastMonthlyBadge,
            type: 'monthly',
        });

        return res.json({
            success: true,
            data: {
                lastAttainedRegularBadge,
                nextRegularBadge,
                nextMonthlyBadge,
            },
        });
    }

    // Dashboard data: all badges with achievement status
    static async getBadgesDashboardData(req, res) {
        const { userID } = req.query;
        const currentZonedDate = req.currentZonedDate;

        // Get all app badges
        const regularBadges = await BadgesRepository.getBadges({ type: 'regular' });
        const monthlyBadges = await BadgesRepository.getBadges({ type: 'monthly' });

        // Get user's earned badges
        const userBadges = await UserBadgesRepository.getUserBadges({ userID });

        // Process and merge regular badges
        const filteredRegularBadges = userBadges.filter(b => b.badge?.type === 'regular');
        const resRegularBadges = sortAndFilterBadges({
            filteredBadges: filteredRegularBadges,
            appBadgesByCategory: regularBadges,
            badgeType: 'regular',
        });

        // Process and merge monthly badges
        const filteredMonthlyBadges = userBadges.filter(b => b.badge?.type === 'monthly');
        const resMonthlyBadges = sortAndFilterBadges({
            filteredBadges: filteredMonthlyBadges,
            appBadgesByCategory: monthlyBadges,
            badgeType: 'monthly',
            currentZonedDate,
        });

        return res.json({
            success: true,
            data: {
                regularBadges: resRegularBadges,
                monthlyBadges: resMonthlyBadges,
            },
        });
    }
}
```

### Helper: sortAndFilterBadges

```typescript
function sortAndFilterBadges({ filteredBadges, appBadgesByCategory, badgeType, currentZonedDate }) {
    let sortedBadges = [];

    // Build count data for earned badges
    const countData = {};
    filteredBadges.forEach((filteredBadge) => {
        const badgeCountData = filteredBadges.filter(b =>
            filteredBadge.badge._id.equals(b.badge._id)
        );
        countData[filteredBadge.badge._id] = {
            firstDateEarned: badgeCountData[0]?.createdAt,
            lastDateEarned: badgeCountData[badgeCountData.length - 1]?.createdAt,
            numberOfTimesEarned: badgeCountData.length,
        };
    });

    // Merge app badges with user achievement data
    for (const appBadge of appBadgesByCategory) {
        const badgeHasBeenAchieved = filteredBadges.some(fb =>
            appBadge._id.equals(fb.badge._id)
        );

        sortedBadges.push({
            ...appBadge,
            badgeHasBeenAchieved,
            firstDateEarned: countData[appBadge._id]?.firstDateEarned || null,
            lastDateEarned: countData[appBadge._id]?.lastDateEarned || null,
            numberOfTimesEarned: countData[appBadge._id]?.numberOfTimesEarned || 0,
        });
    }

    // Sort by priority for regular badges
    if (badgeType === 'regular') {
        sortedBadges.sort((a, b) => a.priority - b.priority);
    }

    // Filter monthly badges to current month + already earned
    if (badgeType === 'monthly') {
        const currentYear = currentZonedDate.getFullYear();
        const currentMonth = currentZonedDate.getMonth() + 1;
        const currSum = currentYear + currentMonth;

        sortedBadges = sortedBadges.filter(badge =>
            (badge.month + badge.year === currSum) || badge.badgeHasBeenAchieved
        );
        sortedBadges.sort((a, b) => (a.year + a.month) - (b.year + b.month));
    }

    return sortedBadges;
}
```

---

## Pub/Sub Messaging

### Configuration

```typescript
import { PubSub } from '@google-cloud/pubsub';

// Environment variables required
const GCP_PROJECT = process.env.GCP_PROJECT;
const PUB_SUB_TOPIC = process.env.PUB_SUB_TOPIC;
const PUB_SUB_SUBSCRIPTION = process.env.PUB_SUB_SUBSCRIPTION;

export const TOPICS = {
    BADGES: PUB_SUB_TOPIC,
};

let pubSubClient: PubSub;

export function getPubSubClient() {
    if (!pubSubClient) {
        pubSubClient = new PubSub({ projectId: GCP_PROJECT });
    }
    return pubSubClient;
}

export async function publishMessage(topicName: string, data: string) {
    const dataBuffer = Buffer.from(data);
    try {
        await getPubSubClient().topic(topicName).publishMessage({ data: dataBuffer });
    } catch (error) {
        console.error(error);
    }
}
```

### Required Environment Variables

```
GCP_PROJECT=your-gcp-project-id
PUB_SUB_TOPIC=badges-topic
PUB_SUB_SUBSCRIPTION=badges-subscription
```

---

## Migration/Seeding Badges

### Regular Badges Seed Data

```typescript
const regularBadgesData = [
    // Strong Start badges
    { name: 'Strong start', level: 1, slug: 'strong-start1', priority: 1, canBeMultiple: true, description: '2 consecutive active days' },
    { name: 'Strong start', level: 2, slug: 'strong-start2', priority: 4, canBeMultiple: true, description: '5 consecutive active days' },
    { name: 'Strong start', level: 3, slug: 'strong-start3', priority: 5, canBeMultiple: true, description: '10 consecutive active days' },
    { name: 'Strong start', level: 4, slug: 'strong-start4', priority: 6, canBeMultiple: true, description: '15 consecutive active days' },

    // Daredevil badges
    { name: 'Daredevil', level: 1, slug: 'daredevil1', priority: 2, canBeMultiple: true, description: 'Max all points in a day' },
    { name: 'Daredevil', level: 2, slug: 'daredevil2', priority: 10, canBeMultiple: true, description: 'Max all points 7 days in a row' },
    { name: 'Daredevil', level: 3, slug: 'daredevil3', priority: 12, canBeMultiple: true, description: 'Max all points 14 days in a row' },
    { name: 'Daredevil', level: 4, slug: 'daredevil4', priority: 13, canBeMultiple: true, description: 'Max all points 30 days in a row' },
    { name: 'Daredevil', level: 5, slug: 'daredevil5', priority: 17, canBeMultiple: true, description: 'Max all points 60 days in a row' },

    // Streak badges
    { name: 'Streak', level: 1, slug: 'streak1', priority: 7, canBeMultiple: true, description: '20 consecutive active days' },
    { name: 'Streak', level: 2, slug: 'streak2', priority: 9, canBeMultiple: true, description: '50 consecutive active days' },
    { name: 'Streak', level: 3, slug: 'streak3', priority: 11, canBeMultiple: true, description: '100 consecutive active days' },
    { name: 'Streak', level: 4, slug: 'streak4', priority: 14, canBeMultiple: true, description: '180 consecutive active days' },
    { name: 'Streak', level: 5, slug: 'streak5', priority: 16, canBeMultiple: true, description: '365 consecutive active days' },

    // Points badges
    { name: 'Decade', slug: 'decade', priority: 3, canBeMultiple: false, description: 'Earn 10 points' },
    { name: 'Century', slug: 'century', priority: 8, canBeMultiple: false, description: 'Earn 100 points' },
    { name: 'Millenium', slug: 'millenium', priority: 15, canBeMultiple: true, description: 'Earn 1000 points' },

    // Warrior badge
    { name: 'The warrior', slug: 'the-warrior', canBeMultiple: false, description: 'When they join the app' },
];
```

### Monthly Badges Seed Data

```typescript
const monthlyBadgesData = [
    {
        name: 'The Dares Challenge',
        slug: 'the-dares-challenge-6-2021',
        month: 6,
        year: 2021,
        type: 'monthly',
        canBeMultiple: false,
        criteria: {
            category: undefined,
            byPoints: false,
            expectedCount: 50,
            expectedPointSum: 0,
        },
        preText: 'Do at least 50 Dares this month!',
    },
    {
        name: 'Sleep Month',
        slug: 'sleep-month-7-2021',
        month: 7,
        year: 2021,
        type: 'monthly',
        canBeMultiple: false,
        criteria: {
            category: 'sleep',
            byPoints: false,
            expectedCount: 10,
            expectedPointSum: 0,
        },
        preText: 'Do at least 10 Sleep Dares in July!',
    },
    // ... more monthly badges
];
```

---

## Implementation Checklist

### Database Setup

- [ ] Create `badges` collection/table with schema
- [ ] Create `user_badges` collection/table with schema
- [ ] Add post-save hook to UserTarget model for Pub/Sub trigger
- [ ] Create indexes on `userID` and `createdAt` for UserBadge

### Badge Seeding

- [ ] Seed all regular badges with correct slugs, priorities, and levels
- [ ] Seed monthly badges for desired months
- [ ] Generate/configure badge image URLs

### Repository Layer

- [ ] Implement BadgesRepository with all methods
- [ ] Implement UserBadgesRepository with all methods
- [ ] Implement `aggregateOpenTargetsByDay` aggregation
- [ ] Implement `getPointSumOverTime` aggregation

### Badge Helper

- [ ] Implement `assignBadgeToUser` with duplicate prevention
- [ ] Implement `processBadgeByDay` core logic
- [ ] Implement all badge-specific methods:
  - [ ] `assignDaredevilBadge` (levels 1-5)
  - [ ] `assignStrongStartBadge` (levels 1-4)
  - [ ] `assignStreakBadge` (levels 1-5)
  - [ ] `assignDecadeBadge`
  - [ ] `assignCenturyBadge`
  - [ ] `assignMilleniumBadge`
  - [ ] `assignMonthlyBadge`
  - [ ] `assignTheWarriorBadge`

### Consumer/Worker

- [ ] Set up Google Cloud Pub/Sub client
- [ ] Create Pub/Sub topic and subscription
- [ ] Implement `badgesConsumer` subscription listener
- [ ] Implement `processMessageFromSubscription` handler

### API Layer

- [ ] Create badge routes
- [ ] Implement `getUserBadges` endpoint
- [ ] Implement `getBadgesDashboardOverview` endpoint
- [ ] Implement `getBadgesDashboardData` endpoint
- [ ] Implement `sortAndFilterBadges` helper

### Environment Configuration

- [ ] Configure `GCP_PROJECT` environment variable
- [ ] Configure `PUB_SUB_TOPIC` environment variable
- [ ] Configure `PUB_SUB_SUBSCRIPTION` environment variable
- [ ] Configure badge image base URLs

### Testing

- [ ] Test badge assignment for each badge type
- [ ] Test consecutive day evaluation
- [ ] Test duplicate prevention (canBeMultiple = false)
- [ ] Test multiple earning (canBeMultiple = true)
- [ ] Test monthly badge category filtering
- [ ] Test API endpoints

---

## Key Implementation Notes

1. **Asynchronous Processing**: Badge assignment is fire-and-forget. Each check runs independently and failures don't affect other checks.

2. **Duplicate Prevention**:
   - `canBeMultiple = false`: Badge can only be earned once ever
   - `canBeMultiple = true`: Badge can be earned multiple times, but only once per day

3. **Day Grouping**: The `dayPlusYear` calculation (`dayOfYear + year`) creates a unique identifier for consecutive day checking that works across year boundaries.

4. **4 Dares Per Day**: The system assumes 4 daily dares. Daredevil badges require completing all 4; other streak badges require at least 1.

5. **Date Handling**: Uses `moment.js` for date calculations. Be consistent with timezone handling.

6. **Error Handling**: Each badge check handles its own errors to prevent one failure from blocking others.

7. **The Warrior Badge**: Called separately when user first accesses the app, not from the Pub/Sub consumer.
