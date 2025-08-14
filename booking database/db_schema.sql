-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jul 23, 2025 at 01:32 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `t3`
--

-- --------------------------------------------------------

--
-- Table structure for table `facilities`
--

CREATE TABLE `facilities` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `category` varchar(100) DEFAULT NULL,
  `parent_facility_id` int(11) DEFAULT NULL,
  `hotel_id` int(11) DEFAULT NULL,
  `icon_svg` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `facilities`
--

INSERT INTO `facilities` (`id`, `name`, `category`, `icon_svg`, `created_at`, `updated_at`) VALUES
(1, 'مواقف سيارات مجانية', 'مواقف', '<svg>...</svg>', '2025-07-22 21:41:44', '2025-07-22 21:41:44'),
(2, 'واي فاي مجاني', 'إنترنت', '<svg>...</svg>', '2025-07-22 21:41:44', '2025-07-22 21:41:44');

-- --------------------------------------------------------

--
-- Table structure for table `hotels`
--

CREATE TABLE `hotels` (
  `id` int(11) NOT NULL,
  `property_id` int(11) DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `region` varchar(100) DEFAULT NULL,
  `postal_code` varchar(20) DEFAULT NULL,
  `address_country` varchar(100) DEFAULT NULL,
  `latitude` decimal(10,8) DEFAULT NULL,
  `longitude` decimal(11,8) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `stars` tinyint(3) UNSIGNED DEFAULT NULL CHECK (`stars` between 1 and 5),
  `rating_value` decimal(3,1) DEFAULT NULL CHECK (`rating_value` between 0 and 10),
  `rating_text` varchar(50) DEFAULT NULL,
  `url` varchar(500) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `hotels`
--

INSERT INTO `hotels` (`id`, `property_id`, `title`, `address`, `region`, `postal_code`, `address_country`, `latitude`, `longitude`, `description`, `stars`, `rating_value`, `rating_text`, `url`, `created_at`, `updated_at`) VALUES
(1, 1, 'استديو أنيق بدخول ذاتي', 'الخرج شارع ثقيف 8658 الطابق الاول, 11942 الخرج, المملكة العربية السعودية', 'منطقة الرياض', '11942', 'السعودية', 24.16544126, 47.32234126, 'يتميز مكان إقامة \"استديو أنيق بدخول ذاتي\" بإطلالة على المدينة ويقع في الخرج، كما يشتمل على واي فاي مجاني...', 3, 9.6, 'استثنائي', 'https://cf.bstatic.com/xdata/images/hotel/max1024x768/507796868.jpg?k=...', '2025-07-22 21:41:25', '2025-07-22 21:41:25');

-- --------------------------------------------------------

--
-- Table structure for table `hotel_facility`
--

CREATE TABLE `hotel_facility` (
  `hotel_id` int(11) NOT NULL,
  `facility_id` int(11) NOT NULL,
  `is_most_famous` tinyint(1) DEFAULT 0,
  `is_sub_facility` tinyint(1) DEFAULT 0,
  `parent_facility_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `hotel_facility`
--

INSERT INTO `hotel_facility` (`hotel_id`, `facility_id`, `is_most_famous`) VALUES
(1, 1, 1),
(1, 2, 1);

-- --------------------------------------------------------

--
-- Table structure for table `images`
--

CREATE TABLE `images` (
  `id` int(11) NOT NULL,
  `hotel_id` int(11) DEFAULT NULL,
  `room_id` int(11) DEFAULT NULL,
  `image_url` varchar(1000) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `images`
--

INSERT INTO `images` (`id`, `hotel_id`, `room_id`, `image_url`, `created_at`) VALUES
(1, 1, NULL, 'https://cf.bstatic.com/xdata/images/hotel/max1024x768/507796823.jpg?k=...', '2025-07-22 21:43:12'),
(2, 1, NULL, 'https://cf.bstatic.com/xdata/images/hotel/max1024x768/507796856.jpg?k=...', '2025-07-22 21:43:12'),
(3, 1, NULL, 'https://cf.bstatic.com/xdata/images/hotel/max1024x768/507796867.jpg?k=...', '2025-07-22 21:43:12'),
(4, 1, NULL, 'https://cf.bstatic.com/xdata/images/hotel/max1024x768/507796854.jpg?k=...', '2025-07-22 21:43:12'),
(5, 1, NULL, 'https://cf.bstatic.com/xdata/images/hotel/max1024x768/507796865.jpg?k=...', '2025-07-22 21:43:12'),
(6, NULL, 1, 'https://cf.bstatic.com/xdata/images/hotel/max1024x768/507796823.jpg?k=...', '2025-07-22 21:43:40'),
(7, NULL, 1, 'https://cf.bstatic.com/xdata/images/hotel/max1024x768/507796856.jpg?k=...', '2025-07-22 21:43:40');

-- --------------------------------------------------------

--
-- Table structure for table `properties`
--

CREATE TABLE `properties` (
  `id` int(11) NOT NULL,
  `type` varchar(50) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `properties`
--

INSERT INTO `properties` (`id`, `type`, `created_at`, `updated_at`) VALUES
(1, 'hotel', '2025-07-22 19:09:43', '2025-07-22 19:09:43');

-- --------------------------------------------------------

--
-- Table structure for table `rooms`
--

CREATE TABLE `rooms` (
  `id` int(11) NOT NULL,
  `hotel_id` int(11) NOT NULL,
  `room_name` varchar(255) NOT NULL,
  `bed_type` varchar(255) DEFAULT NULL,
  `adult_count` tinyint(3) UNSIGNED NOT NULL DEFAULT 0,
  `children_count` tinyint(3) UNSIGNED NOT NULL DEFAULT 0,
  `content_text` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`content_text`)),
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `rooms`
--

INSERT INTO `rooms` (`id`, `hotel_id`, `room_name`, `bed_type`, `adult_count`, `children_count`, `content_text`, `created_at`, `updated_at`) VALUES
(1, 1, 'شقة استوديو', '1 سرير مزدوج كبير', 2, 1, '{\"مساحة الغرفة\":\"60 م²\",\"وصف الغرفة\":\"This apartment...\",\"الحمام\":[\"لوازم استحمام مجانية\"],\"المرافق المتوفرة\":[\"تكييف\"]}', '2025-07-22 21:43:23', '2025-07-22 21:43:23');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `facilities`
--
ALTER TABLE `facilities`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_facilities_parent` (`parent_facility_id`),
  ADD KEY `idx_facilities_hotel_id` (`hotel_id`);

--
-- Indexes for table `hotels`
--
ALTER TABLE `hotels`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_hotels_property_id` (`property_id`),
  ADD KEY `idx_hotels_location` (`latitude`,`longitude`),
  ADD KEY `idx_hotels_rating` (`rating_value`);

--
-- Indexes for table `hotel_facility`
--
ALTER TABLE `hotel_facility`
  ADD PRIMARY KEY (`hotel_id`,`facility_id`),
  ADD KEY `facility_id` (`facility_id`),
  ADD KEY `idx_hotel_facility` (`hotel_id`,`facility_id`),
  ADD KEY `idx_hotel_facility_parent` (`parent_facility_id`);

--
-- Indexes for table `images`
--
ALTER TABLE `images`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_images_hotel_id` (`hotel_id`),
  ADD KEY `idx_images_room_id` (`room_id`);

--
-- Indexes for table `properties`
--
ALTER TABLE `properties`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `rooms`
--
ALTER TABLE `rooms`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_rooms_hotel_id` (`hotel_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `facilities`
--
ALTER TABLE `facilities`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `hotels`
--
ALTER TABLE `hotels`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `images`
--
ALTER TABLE `images`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- Properties table - ID is now manually managed to match hotel ID
--
ALTER TABLE `properties`
  MODIFY `id` int(11) NOT NULL;

--
-- AUTO_INCREMENT for table `rooms`
--
ALTER TABLE `rooms`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `hotels`
--
ALTER TABLE `hotels`
  ADD CONSTRAINT `hotels_ibfk_1` FOREIGN KEY (`property_id`) REFERENCES `properties` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `facilities`
--
ALTER TABLE `facilities`
  ADD CONSTRAINT `facilities_parent_fk` FOREIGN KEY (`parent_facility_id`) REFERENCES `facilities` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `facilities_hotel_fk` FOREIGN KEY (`hotel_id`) REFERENCES `hotels` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `hotel_facility`
--
ALTER TABLE `hotel_facility`
  ADD CONSTRAINT `hotel_facility_ibfk_1` FOREIGN KEY (`hotel_id`) REFERENCES `hotels` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `hotel_facility_ibfk_2` FOREIGN KEY (`facility_id`) REFERENCES `facilities` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `hotel_facility_parent_fk` FOREIGN KEY (`parent_facility_id`) REFERENCES `facilities` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `images`
--
ALTER TABLE `images`
  ADD CONSTRAINT `images_ibfk_1` FOREIGN KEY (`hotel_id`) REFERENCES `hotels` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `images_ibfk_2` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `rooms`
--
ALTER TABLE `rooms`
  ADD CONSTRAINT `rooms_ibfk_1` FOREIGN KEY (`hotel_id`) REFERENCES `hotels` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
