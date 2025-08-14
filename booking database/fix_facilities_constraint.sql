-- CRITICAL FIX: Remove UNIQUE constraint on facilities.name
-- This is causing the "Duplicate entry" errors you're seeing

-- Remove the UNIQUE constraint that prevents hotels from having same facility names
ALTER TABLE `facilities` DROP INDEX IF EXISTS `name`;

-- Verify the constraint is removed (optional check)
-- You can run this to confirm the index is gone:
-- SHOW INDEX FROM `facilities` WHERE Key_name = 'name'; 