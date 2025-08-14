    -- Database Migration for Booking Hotels
    -- Changes for facilities and properties tables

    -- ========================================
-- 1. PROPERTIES TABLE CHANGES
-- ========================================

-- Remove UNIQUE constraint on type field since each hotel needs its own property
ALTER TABLE `properties` 
DROP INDEX `type`;

-- Remove AUTO_INCREMENT from properties table
ALTER TABLE `properties` 
MODIFY `id` int(11) NOT NULL;

-- Reset auto-increment counter
ALTER TABLE `properties` 
AUTO_INCREMENT = 1;

    -- ========================================
    -- 2. FACILITIES TABLE CHANGES
    -- ========================================

    -- Add parent_facility_id to facilities table to support hierarchy
    ALTER TABLE `facilities` 
    ADD COLUMN `parent_facility_id` int(11) DEFAULT NULL AFTER `category`;

    -- Add hotel_id to facilities table to associate facilities with specific hotels
    ALTER TABLE `facilities` 
    ADD COLUMN `hotel_id` int(11) DEFAULT NULL AFTER `parent_facility_id`;

    -- Add index for parent_facility_id
    ALTER TABLE `facilities`
    ADD KEY `idx_facilities_parent` (`parent_facility_id`);

    -- Add index for hotel_id
    ALTER TABLE `facilities`
    ADD KEY `idx_facilities_hotel_id` (`hotel_id`);

    -- Add foreign key constraint for parent_facility_id
    ALTER TABLE `facilities`
    ADD CONSTRAINT `facilities_parent_fk` 
    FOREIGN KEY (`parent_facility_id`) REFERENCES `facilities` (`id`) ON DELETE CASCADE;

    -- Add foreign key constraint for hotel_id
    ALTER TABLE `facilities`
    ADD CONSTRAINT `facilities_hotel_fk` 
    FOREIGN KEY (`hotel_id`) REFERENCES `hotels` (`id`) ON DELETE CASCADE;

    -- ========================================
    -- 3. HOTEL_FACILITY TABLE CHANGES
    -- ========================================

    -- Add is_sub_facility column to distinguish main facilities from sub-facilities
    ALTER TABLE `hotel_facility` 
    ADD COLUMN `is_sub_facility` tinyint(1) DEFAULT 0 AFTER `is_most_famous`;

    -- Add parent_facility_id to show relationship in hotel_facility junction table
    ALTER TABLE `hotel_facility` 
    ADD COLUMN `parent_facility_id` int(11) DEFAULT NULL AFTER `is_sub_facility`;

    -- Add index for parent_facility_id in hotel_facility table
    ALTER TABLE `hotel_facility`
    ADD KEY `idx_hotel_facility_parent` (`parent_facility_id`);

    -- Add foreign key constraint for parent_facility_id in hotel_facility table
    ALTER TABLE `hotel_facility`
    ADD CONSTRAINT `hotel_facility_parent_fk` 
    FOREIGN KEY (`parent_facility_id`) REFERENCES `facilities` (`id`) ON DELETE SET NULL; 