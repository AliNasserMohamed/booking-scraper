-- Quick fix for current database issues
-- Run this to fix the errors you're experiencing

-- Fix 1: Remove UNIQUE constraint on properties.type
ALTER TABLE `properties` DROP INDEX IF EXISTS `type`;

-- Fix 2: Remove UNIQUE constraint on facilities.name (CRITICAL FIX)
ALTER TABLE `facilities` DROP INDEX IF EXISTS `name`;

-- Fix 3: Ensure properties table doesn't require AUTO_INCREMENT for id
ALTER TABLE `properties` MODIFY `id` int(11) NOT NULL;

-- Clear any existing property records to avoid conflicts
DELETE FROM `properties`;

-- Reset AUTO_INCREMENT counter
ALTER TABLE `properties` AUTO_INCREMENT = 1; 