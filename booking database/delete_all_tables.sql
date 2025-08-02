-- Delete All Data from Hotel Parser Tables
-- Execute these queries in this exact order to respect foreign key constraints

-- 1. Delete junction table first (references hotels and facilities)
DELETE FROM hotel_facility;

-- 2. Delete images (references hotels and rooms)
DELETE FROM images;

-- 3. Delete rooms (references hotels)
DELETE FROM rooms;

-- 4. Delete hotels (references properties)
DELETE FROM hotels;

-- 5. Delete facilities (referenced by hotel_facility, but that's already deleted)
DELETE FROM facilities;

-- 6. Delete properties (referenced by hotels, but that's already deleted)
DELETE FROM properties;

-- Optional: Reset auto-increment counters if needed
-- ALTER TABLE hotel_facility AUTO_INCREMENT = 1;
-- ALTER TABLE images AUTO_INCREMENT = 1;
-- ALTER TABLE rooms AUTO_INCREMENT = 1;
-- ALTER TABLE hotels AUTO_INCREMENT = 1;
-- ALTER TABLE facilities AUTO_INCREMENT = 1;
-- ALTER TABLE properties AUTO_INCREMENT = 1;

-- Verification queries (uncomment to check if tables are empty)
-- SELECT COUNT(*) as hotel_facility_count FROM hotel_facility;
-- SELECT COUNT(*) as images_count FROM images;
-- SELECT COUNT(*) as rooms_count FROM rooms;
-- SELECT COUNT(*) as hotels_count FROM hotels;
-- SELECT COUNT(*) as facilities_count FROM facilities;
-- SELECT COUNT(*) as properties_count FROM properties; 