## ADDED Requirements

### Requirement: Create weekly task template
The system SHALL allow parents to create task templates assigned to a specific child and weekday.

#### Scenario: Create a written task template
- **WHEN** parent provides child_id, weekday (1-7), title "数学口算", type "written", description "2页", and points 5
- **THEN** system creates a task template record with sort_order auto-assigned

#### Scenario: Create a reading task template
- **WHEN** parent provides child_id, weekday, title "英语阅读", type "reading", and points 3
- **THEN** system creates a task template with type "reading"

### Requirement: Update task template
The system SHALL allow parents to modify existing task templates.

#### Scenario: Update template fields
- **WHEN** parent updates title, type, description, points, or sort_order of a template
- **THEN** system persists changes; changes take effect from the next daily task generation

### Requirement: Delete task template
The system SHALL allow parents to delete task templates.

#### Scenario: Delete existing template
- **WHEN** parent deletes a template
- **THEN** system removes the template; already-generated daily tasks are not affected

### Requirement: List task templates by child
The system SHALL return all task templates for a child, grouped by weekday.

#### Scenario: Query templates
- **WHEN** user requests templates for a child
- **THEN** system returns templates grouped by weekday (1-7), ordered by sort_order within each day

### Requirement: Conditional task configuration
The system SHALL allow parents to create conditional tasks that trigger when all required daily tasks are completed.

#### Scenario: Create conditional task
- **WHEN** parent provides child_id, title "画画", type "written", description "30分钟", points 5, trigger_condition "all_required_done"
- **THEN** system creates a conditional task template

#### Scenario: List conditional tasks
- **WHEN** user requests conditional tasks for a child
- **THEN** system returns all conditional task templates for that child

### Requirement: Voice input for task management
The system SHALL accept natural language text (from STT) and parse it into structured task operations.

#### Scenario: Voice create command
- **WHEN** parent sends text "每周一给大宝添加数学口算，5积分"
- **THEN** system returns parsed intent: {action: "create", child: "大宝", weekday: 1, title: "数学口算", points: 5} for user confirmation

#### Scenario: Voice delete command
- **WHEN** parent sends text "把周三的英语阅读删掉"
- **THEN** system returns parsed intent: {action: "delete", weekday: 3, title: "英语阅读"} for user confirmation

#### Scenario: Unparseable input
- **WHEN** the LLM cannot extract a valid intent from the text
- **THEN** system returns error with suggestion to rephrase
