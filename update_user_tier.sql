-- Update user subscription tier
-- Usage examples:
-- 1. Set specific user to pro: UPDATE users SET subscription_tier = 'pro' WHERE id = 644554733;
-- 2. Set all users to pro (testing): UPDATE users SET subscription_tier = 'pro';
-- 3. Reset all to free: UPDATE users SET subscription_tier = 'free';

-- Set your user to pro tier for testing
UPDATE users
SET subscription_tier = 'pro'
WHERE id = 644554733;

-- Verify update
SELECT id, username, first_name, subscription_tier, created_at
FROM users
WHERE id = 644554733;
