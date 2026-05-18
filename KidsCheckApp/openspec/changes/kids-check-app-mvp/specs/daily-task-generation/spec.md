## ADDED Requirements

### Requirement: Scheduled daily task generation
The system SHALL automatically generate daily task instances from templates at 00:00 UTC+8 each day.

#### Scenario: Normal daily generation
- **WHEN** the scheduler runs at 00:00 on a Wednesday (weekday=3)
- **THEN** system creates one daily_task record per template matching weekday=3 for each child, all with status "pending"

#### Scenario: No templates for today
- **WHEN** a child has no templates configured for today's weekday
- **THEN** system creates no daily tasks for that child (empty task list is valid)

### Requirement: Fallback generation on first access
The system SHALL generate tasks on-demand if scheduled generation was missed.

#### Scenario: Client requests today's tasks but none exist
- **WHEN** client requests daily tasks for a child for today and no records exist for today
- **THEN** system triggers generation for today before returning the task list

### Requirement: Conditional task dynamic insertion
The system SHALL insert conditional tasks into the daily task list when all required tasks are completed.

#### Scenario: All required tasks completed
- **WHEN** the last required daily task is marked as done
- **THEN** system creates daily_task records from all conditional_task templates for that child with status "pending" and today's date

#### Scenario: Some required tasks still pending
- **WHEN** a required task is completed but others remain pending
- **THEN** system does not insert conditional tasks

### Requirement: Idempotent generation
The system SHALL not create duplicate daily tasks if generation runs multiple times.

#### Scenario: Duplicate generation attempt
- **WHEN** generation is triggered for a child+date combination that already has tasks
- **THEN** system skips creation and returns existing tasks
