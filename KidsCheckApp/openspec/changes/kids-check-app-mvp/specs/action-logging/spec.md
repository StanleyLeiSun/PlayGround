## ADDED Requirements

### Requirement: Log all user actions
The system SHALL record every user operation as an action log entry containing timestamp, user identity, and action description.

#### Scenario: Login action logged
- **WHEN** a user successfully logs in
- **THEN** system creates an action_log record with user_id, action="login", target_type=null, target_id=null, created_at=current timestamp

#### Scenario: Check-in action logged
- **WHEN** a user completes a check-in for a task
- **THEN** system creates an action_log record with user_id, action="check_in", target_type="daily_task", target_id=task id, metadata={child_id, photo_uploaded: true/false}

#### Scenario: Template creation logged
- **WHEN** a parent creates a task template
- **THEN** system creates an action_log record with user_id, action="create_template", target_type="task_template", target_id=template id, metadata={child_id, weekday, title}

#### Scenario: Template modification logged
- **WHEN** a parent updates or deletes a task template
- **THEN** system creates an action_log record with action="update_template" or "delete_template", target_type="task_template", target_id=template id

#### Scenario: Reward redemption logged
- **WHEN** a user redeems points for a reward
- **THEN** system creates an action_log record with action="redeem_reward", target_type="reward", target_id=reward id, metadata={child_id, points_spent}

#### Scenario: Photo review logged
- **WHEN** a parent reviews a check-in photo
- **THEN** system creates an action_log record with action="review_photo", target_type="check_in_photo", target_id=photo id, metadata={result: "valid"/"needs-redo"}

### Requirement: Action log is append-only
The system SHALL NOT allow updating or deleting action log records.

#### Scenario: No delete endpoint
- **WHEN** any user attempts to delete or modify an action_log record
- **THEN** system returns error 405

### Requirement: Query action logs
The system SHALL allow parents to query action logs with filters.

#### Scenario: Query by user
- **WHEN** a parent requests logs filtered by user_id
- **THEN** system returns matching logs ordered by created_at descending, paginated

#### Scenario: Query by date range
- **WHEN** a parent requests logs filtered by date range
- **THEN** system returns logs within the specified time window

#### Scenario: Grandparent cannot query logs
- **WHEN** a grandparent attempts to query action logs
- **THEN** system returns error 403
