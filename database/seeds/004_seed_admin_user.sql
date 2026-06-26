-- ============================================================
-- Seed: Default admin user
-- ============================================================
-- Password: Admin@12345
-- bcrypt hash generated with cost factor 12
-- IMPORTANT: Change this password immediately after first login!
-- ============================================================

INSERT INTO users (
    email,
    username,
    password_hash,
    full_name,
    role_id,
    department_id,
    is_active
) VALUES (
    'admin@helpdesk.local',
    'admin',
    '\$2b$12$LQv3c1yqBwEHxv6mZJ8Z8O7P8N5dQEzKYpJ9BqEcMmqRxQ0vSXmFu',  -- bcrypt of "Admin@12345"
    'System Administrator',
    (SELECT id FROM roles WHERE name = 'admin'),
    (SELECT id FROM departments WHERE name = 'IT Support'),
    TRUE
)
ON CONFLICT (email) DO NOTHING;