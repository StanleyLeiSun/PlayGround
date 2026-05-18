## ADDED Requirements

### Requirement: Daily progress overview
The system SHALL provide a summary of task completion for a child on a given date.

#### Scenario: Query progress for today
- **WHEN** user requests progress for a child for today
- **THEN** system returns: total task count, completed count, list of tasks with status/completed_at/completed_by, and today's earned points

#### Scenario: Query progress for past date (parent only)
- **WHEN** a parent requests progress for a child for a past date
- **THEN** system returns the same structure as today's query for the specified date

#### Scenario: Grandparent queries past date
- **WHEN** a grandparent requests progress for a past date
- **THEN** system returns error 403 (grandparents can only view current day)

### Requirement: Photo review
The system SHALL allow parents to view check-in photos and mark them as reviewed.

#### Scenario: View photo list for a day
- **WHEN** parent requests photos for a child on a given date
- **THEN** system returns list of check_in_photo records with photo URLs, task names, and review status

#### Scenario: Mark photo as reviewed
- **WHEN** parent marks a photo as "valid" or "needs-redo" with optional note
- **THEN** system updates the check_in_photo record's reviewed flag and review_note

### Requirement: Timeline view data
The system SHALL return tasks ordered by completion time for timeline display.

#### Scenario: Completed tasks in timeline
- **WHEN** client requests timeline for a date
- **THEN** system returns completed tasks ordered by completed_at (ascending), followed by pending tasks with null completed_at
