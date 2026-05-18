## 1. Project Setup

- [ ] 1.1 Initialize FastAPI project structure (main.py, routers/, models/, schemas/, services/, config.py)
- [ ] 1.2 Configure PostgreSQL connection with SQLAlchemy async (database.py, alembic for migrations)
- [ ] 1.3 Create Alembic migration for all 11 tables (family, user, child, task_template, conditional_task, daily_task, check_in_photo, point_account, point_transaction, reward, reward_redemption)
- [ ] 1.4 Setup JWT authentication middleware (auth.py: token generation, validation, role extraction)
- [ ] 1.5 Setup file upload directory structure and static file serving for photos
- [ ] 1.6 Initialize Android project with Kotlin + Jetpack Compose, configure Retrofit HTTP client

## 2. Family Management

- [ ] 2.1 Implement POST /api/auth/register (create user + family, return JWT)
- [ ] 2.2 Implement POST /api/auth/login (validate credentials, return JWT)
- [ ] 2.3 Implement POST /api/family/invite-code (generate 6-char code with 24h expiry)
- [ ] 2.4 Implement POST /api/auth/join-family (validate invite code, assign grandparent role)
- [ ] 2.5 Implement CRUD endpoints for children: GET/POST /api/children, PUT/DELETE /api/children/{id}
- [ ] 2.6 Implement role-based access control decorator (parent-only guard for protected endpoints)
- [ ] 2.7 Write tests: registration, login, invite flow, child CRUD, RBAC enforcement

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
- [ ] 5.5 Implement GET /api/progress/{child_id}/photo/{id} (authenticated photo retrieval with family check)
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

## 8. Android Client

- [ ] 8.1 Build login/register screens with Compose (phone + password form, token storage)
- [ ] 8.2 Build bottom navigation (3 tabs: 今日任务, 进度, 我的)
- [ ] 8.3 Build today's task list screen (child switch tabs, task cards, pending/done states)
- [ ] 8.4 Build check-in bottom sheet (photo capture for written, confirm-only for reading, celebration animation)
- [ ] 8.5 Build progress screen (date picker, progress bar, timeline, photo thumbnails)
- [ ] 8.6 Build "我的" screen (family info, child points, menu items with role-based visibility)
- [ ] 8.7 Build task template management screen (weekday groups, conditional tasks section)
- [ ] 8.8 Build voice input integration (Android STT → API call → confirmation card)
- [ ] 8.9 Build rewards screen (reward list, redeem button, point balance display)
- [ ] 8.10 Build family management screen (child profiles, invite code generation/display)
- [ ] 8.11 Implement offline caching for today's task list (Room database)
- [ ] 8.12 Implement photo compression before upload (max 1MB)

## 9. Integration and Deployment

- [ ] 9.1 End-to-end testing: complete flow from registration → template setup → daily generation → check-in → progress view
- [ ] 9.2 Configure production deployment (systemd service, nginx reverse proxy, HTTPS)
- [ ] 9.3 Setup PostgreSQL backup schedule (daily pg_dump)
- [ ] 9.4 Write API documentation (FastAPI auto-generated OpenAPI/Swagger)
