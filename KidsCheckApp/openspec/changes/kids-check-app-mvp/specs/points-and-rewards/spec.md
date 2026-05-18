## ADDED Requirements

### Requirement: Automatic point awarding on task completion
The system SHALL automatically add points to a child's account when a task is checked in.

#### Scenario: Points awarded on check-in
- **WHEN** a daily task with points value 5 is marked as done
- **THEN** system adds 5 to the child's point_account balance and creates a point_transaction record with positive amount, reason "task_completed", and reference to the daily_task

#### Scenario: No double awarding
- **WHEN** points have already been awarded for a task (transaction exists)
- **THEN** system does not create duplicate transaction

### Requirement: Point balance query
The system SHALL provide current point balance and transaction history for a child.

#### Scenario: Query balance
- **WHEN** user requests points for a child
- **THEN** system returns current balance and recent transaction list (paginated, newest first)

### Requirement: Reward management
The system SHALL allow parents to create, update, and delete rewards in the family reward library.

#### Scenario: Create reward
- **WHEN** parent provides title "看一集动画片", cost_points 10, description
- **THEN** system creates a reward record linked to the family

#### Scenario: Update reward
- **WHEN** parent updates title, cost, or description of a reward
- **THEN** system persists changes

#### Scenario: Delete reward
- **WHEN** parent deletes a reward
- **THEN** system removes the reward; existing redemption records are not affected

### Requirement: Point redemption
The system SHALL allow users to redeem points for rewards.

#### Scenario: Successful redemption
- **WHEN** user selects a reward (cost 10) for a child with balance 15
- **THEN** system deducts 10 from balance, creates point_transaction with negative amount and reason "reward_redeemed", and creates reward_redemption record with status "pending"

#### Scenario: Insufficient points
- **WHEN** user selects a reward (cost 30) for a child with balance 20
- **THEN** system returns error 400 indicating insufficient points

### Requirement: Redemption fulfillment
The system SHALL allow parents to confirm reward delivery.

#### Scenario: Parent confirms fulfillment
- **WHEN** parent marks a pending redemption as fulfilled
- **THEN** system updates reward_redemption status to "fulfilled" with timestamp

#### Scenario: Non-parent attempts fulfillment
- **WHEN** grandparent attempts to mark redemption as fulfilled
- **THEN** system returns error 403
