## 1. Project Setup

- [ ] 1.1 Initialize FastAPI project structure (main.py, routers/, models/, schemas/, services/, config.py)
- [ ] 1.2 Configure PostgreSQL connection with SQLAlchemy async (database.py, alembic for migrations)
- [ ] 1.3 Create Alembic migration for tables: user, child, task_template, conditional_task, daily_task, check_in_photo, point_account, point_transaction, reward, reward_redemption
- [ ] 1.4 Create seed data migration: 6 users (爸爸/妈妈 role=parent, 爷爷/奶奶/姥姥/姥爷 role=grandparent, password=123456 hashed), 2 children (萝卜 age=8, 蚕豆 age=5), 2 point accounts (balance=0)
- [ ] 1.5 Setup JWT authentication middleware (auth.py: token generation, validation, role extraction)
- [ ] 1.6 Setup file upload directory structure and static file serving for photos
- [ ] 1.7 Initialize Android project with Kotlin + Jetpack Compose, configure Retrofit HTTP client

## 2. Authentication

- [ ] 2.1 Implement POST /api/auth/login (accept username + password, validate against seeded users, return JWT)
- [ ] 2.2 Implement GET /api/auth/me (return current user info with role)
- [ ] 2.3 Implement role-based access control decorator (parent-only guard for protected endpoints)
- [ ] 2.4 Write tests: login success/failure, token validation, RBAC enforcement

## 3. Task Template Management

- [ ] 3.1 Implement GET /api/templates/{child_id} (return templates grouped by weekday)
- [ ] 3.2 Implement POST /api/templates/{child_id} (create template with weekday, title, type, points)
- [ ] 3.3 Implement PUT /api/templates/{id} and DELETE /api/templates/{id}
- [ ] 3.4 Implement GET/POST /api/conditional-tasks/{child_id} (conditional task CRUD)
- [ ] 3.5 Implement POST /api/templates/voice (send text to LLM, return parsed intent JSON)
- [ ] 3.6 Write tests: template CRUD, conditional task CRUD, voice parsing with mock LLM

## 4. Daily Task Generation

- [ ] 4.1 Implement daily task generation service (query templates by weekday, create daily_task records)
- [ ] 4.2 Configure APScheduler to run generation at 00:00 UTC+8 daily
- [ ] 4.3 Implement fallback generation in GET /api/daily-tasks/{child_id}/{date} (generate if none exist)
- [ ] 4.4 Implement idempotency check (skip if tasks already exist for child+date)
- [ ] 4.5 Implement conditional task insertion trigger (called after each check-in, check all required done)
- [ ] 4.6 Write tests: scheduled generation, fallback, idempotency, conditional trigger

## 5. Check-in Flow

- [ ] 5.1 Implement POST /api/daily-tasks/{id}/check-in (validate task status, handle photo requirement by type)
- [ ] 5.2 Implement photo upload handling (compress validation, UUID naming, store to filesystem)
- [ ] 5.3 Implement check_in_photo record creation with photo_url, uploaded_by, uploaded_at
- [ ] 5.4 Implement duplicate check-in prevention (409 if already done)
- [ ] 5.5 Implement GET /api/progress/{child_id}/photo/{id} (authenticated photo retrieval)
- [ ] 5.6 Wire point awarding into check-in flow (call points service after successful check-in)
- [ ] 5.7 Wire conditional task trigger into check-in flow (check and insert if all required done)
- [ ] 5.8 Write tests: check-in with/without photo, duplicate prevention, photo access control

## 6. Progress Tracking

- [ ] 6.1 Implement GET /api/progress/{child_id}/{date} (return task list with status, timeline order, points summary)
- [ ] 6.2 Implement date restriction for grandparent role (only today allowed)
- [ ] 6.3 Implement photo review: PUT /api/progress/{child_id}/photo/{id}/review (mark valid/needs-redo)
- [ ] 6.4 Write tests: progress query, role-based date restriction, photo review

## 7. Points and Rewards

- [ ] 7.1 Implement point awarding service (add to balance, create transaction, idempotency via task reference)
- [ ] 7.2 Implement GET /api/points/{child_id} (balance + paginated transaction history)
- [ ] 7.3 Implement CRUD for rewards: GET/POST /api/rewards, PUT/DELETE /api/rewards/{id}
- [ ] 7.4 Implement POST /api/rewards/{id}/redeem (balance check, deduct, create redemption with pending status)
- [ ] 7.5 Implement PUT /api/rewards/redemptions/{id}/fulfill (parent-only, mark as fulfilled)
- [ ] 7.6 Write tests: point awarding, balance query, redemption flow, insufficient points, RBAC

## 8. Action Logging

- [ ] 8.1 Create action_log table migration (id, user_id, action, target_type, target_id, metadata JSON, created_at)
- [ ] 8.2 Implement ActionLogService (async append-only writes, no update/delete)
- [ ] 8.3 Add logging calls to all endpoints: login, check-in, template CRUD, reward redeem, photo review
- [ ] 8.4 Implement GET /api/action-logs (parent-only, filterable by user_id/date range, paginated)
- [ ] 8.5 Write tests: log creation on each action type, query filters, RBAC enforcement

## 9. Android Client

- [ ] 9.1 Build login screen (user list selector + password input, token storage)
- [ ] 9.2 Build bottom navigation (3 tabs: 今日任务, 进度, 我的)
- [ ] 9.3 Build today's task list screen (child switch tabs: 萝卜/蚕豆, task cards, pending/done states)
- [ ] 9.4 Build check-in bottom sheet (photo capture for written, confirm-only for reading, celebration animation)
- [ ] 9.5 Build progress screen (date picker, progress bar, timeline, photo thumbnails)
- [ ] 9.6 Build "我的" screen (child points, menu items with role-based visibility)
- [ ] 9.7 Build task template management screen (weekday groups, conditional tasks section, parent-only)
- [ ] 9.8 Build voice input integration (Android STT → API call → confirmation card)
- [ ] 9.9 Build rewards screen (reward list, redeem button, point balance display)
- [ ] 9.10 Implement offline caching for today's task list (Room database)
- [ ] 9.11 Implement photo compression before upload (max 1MB)

## 10. Integration and Deployment

- [ ] 10.1 End-to-end testing: login → template setup → daily generation → check-in → progress view
- [ ] 10.2 Configure production deployment (systemd service, nginx reverse proxy, HTTPS)
- [ ] 10.3 Setup PostgreSQL backup schedule (daily pg_dump)
- [ ] 10.4 Write API documentation (FastAPI auto-generated OpenAPI/Swagger)
