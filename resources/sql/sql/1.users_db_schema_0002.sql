BEGIN;

CREATE TABLE `annotation` (`created_at` datetime(6) NULL, `updated_at` datetime(6) NULL, `created_by` varchar(50) NULL, `updated_by` varchar(50) NULL, `is_active` integer NOT NULL, `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `source` varchar(255) NULL, `source_version` varchar(255) NULL, `annotation` varchar(255) NULL, `annotation_version` varchar(255) NULL);
CREATE TABLE `bam` (`created_at` datetime(6) NULL, `updated_at` datetime(6) NULL, `created_by` varchar(50) NULL, `updated_by` varchar(50) NULL, `is_active` integer NOT NULL, `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `filename` varchar(255) NULL, `key` varchar(255) NULL, `sample` varchar(255) NULL);
CREATE TABLE `bookmarks` (`created_at` datetime(6) NULL, `updated_at` datetime(6) NULL, `created_by` varchar(50) NULL, `updated_by` varchar(50) NULL, `is_active` integer NOT NULL, `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `query` longtext NOT NULL, `description` varchar(255) NOT NULL, `long_description` longtext NOT NULL);
CREATE TABLE `db_accesses` (`created_at` datetime(6) NULL, `updated_at` datetime(6) NULL, `created_by` varchar(50) NULL, `updated_by` varchar(50) NULL, `is_active` integer NOT NULL, `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY);
CREATE TABLE `history` (`created_at` datetime(6) NULL, `updated_at` datetime(6) NULL, `created_by` varchar(50) NULL, `updated_by` varchar(50) NULL, `is_active` integer NOT NULL, `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `session_start` datetime(6) NOT NULL, `url` longtext NOT NULL, `query` longtext NOT NULL, `description` varchar(255) NOT NULL, `long_description` longtext NOT NULL, `ip_address` varchar(255) NOT NULL);
CREATE TABLE `people` (`created_at` datetime(6) NULL, `updated_at` datetime(6) NULL, `created_by` varchar(50) NULL, `updated_by` varchar(50) NULL, `is_active` integer NOT NULL, `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `firstname` varchar(255) NOT NULL, `lastname` varchar(255) NOT NULL, `institution` varchar(255) NULL, `street` varchar(255) NULL, `city` varchar(255) NULL, `phone` varchar(30) NULL, `is_laboratory` integer NULL, `laboratory_id` integer NULL);
CREATE TABLE `preferences` (`created_at` datetime(6) NULL, `updated_at` datetime(6) NULL, `created_by` varchar(50) NULL, `updated_by` varchar(50) NULL, `is_active` integer NOT NULL, `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `preferences` longtext NOT NULL, `description` longtext NOT NULL);
CREATE TABLE `roles` (`created_at` datetime(6) NULL, `updated_at` datetime(6) NULL, `created_by` varchar(50) NULL, `updated_by` varchar(50) NULL, `is_active` integer NOT NULL, `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(255) NOT NULL, `rank` integer NULL, `can_validate_user` integer NOT NULL, `can_delete_user` integer NOT NULL);
CREATE TABLE `users` (`created_at` datetime(6) NULL, `updated_at` datetime(6) NULL, `created_by` varchar(50) NULL, `updated_by` varchar(50) NULL, `is_active` integer NOT NULL, `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `username` varchar(25) NOT NULL UNIQUE, `password` varchar(255) NOT NULL, `salt` varchar(255) NOT NULL, `email` varchar(255) NOT NULL, `code` varchar(25) NOT NULL, `activation_code` varchar(25) NULL, `is_password_reset` integer NULL, `person_id` integer NULL, `role_id` integer NULL);
CREATE TABLE `variants_db` (`created_at` datetime(6) NULL, `updated_at` datetime(6) NULL, `created_by` varchar(50) NULL, `updated_by` varchar(50) NULL, `is_active` integer NOT NULL, `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `name` varchar(255) NOT NULL, `visible_name` varchar(255) NULL, `filename` varchar(255) NULL, `location` longtext NULL, `hash` varchar(255) NULL, `description` longtext NULL, `size` bigint NULL, `parent_db_id` integer NULL);

-- Alter unique_together for variantsdb (1 constraint(s))
ALTER TABLE `variants_db` ADD CONSTRAINT `variants_db_filename_5696cb9a_uniq` UNIQUE (`filename`, `hash`);
-- Add field user to preferences
ALTER TABLE `preferences` ADD COLUMN `user_id` integer NULL;
ALTER TABLE `preferences` ALTER COLUMN `user_id` DROP DEFAULT;
-- Add field user to history
ALTER TABLE `history` ADD COLUMN `user_id` integer NULL;
ALTER TABLE `history` ALTER COLUMN `user_id` DROP DEFAULT;
-- Add field user to dbaccess
ALTER TABLE `db_accesses` ADD COLUMN `user_id` integer NULL;
ALTER TABLE `db_accesses` ALTER COLUMN `user_id` DROP DEFAULT;
-- Add field variants_db to dbaccess
ALTER TABLE `db_accesses` ADD COLUMN `variants_db_id` integer NULL;
ALTER TABLE `db_accesses` ALTER COLUMN `variants_db_id` DROP DEFAULT;
-- Add field db_access to bookmarks
ALTER TABLE `bookmarks` ADD COLUMN `db_access_id` integer NULL;
ALTER TABLE `bookmarks` ALTER COLUMN `db_access_id` DROP DEFAULT;
-- Add field variants_db to bam
ALTER TABLE `bam` ADD COLUMN `variants_db_id` integer NULL;
ALTER TABLE `bam` ALTER COLUMN `variants_db_id` DROP DEFAULT;
-- Add field variants_db to annotation
ALTER TABLE `annotation` ADD COLUMN `variants_db_id` integer NULL;
ALTER TABLE `annotation` ALTER COLUMN `variants_db_id` DROP DEFAULT;

-- Alter unique_together for dbaccess (1 constraint(s))
ALTER TABLE `db_accesses` ADD CONSTRAINT `db_accesses_user_id_974a5ce8_uniq` UNIQUE (`user_id`, `variants_db_id`);

ALTER TABLE `people` ADD CONSTRAINT `people_laboratory_id_2e90f6d4_fk_people_id` FOREIGN KEY (`laboratory_id`) REFERENCES `people` (`id`);
ALTER TABLE `users` ADD CONSTRAINT `users_person_id_5146b3bd_fk_people_id` FOREIGN KEY (`person_id`) REFERENCES `people` (`id`);
ALTER TABLE `users` ADD CONSTRAINT `users_role_id_1900a745_fk_roles_id` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`);
CREATE INDEX `preferences_e8701ad4` ON `preferences` (`user_id`);
ALTER TABLE `preferences` ADD CONSTRAINT `preferences_user_id_9015d1e0_fk_users_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);
CREATE INDEX `history_e8701ad4` ON `history` (`user_id`);
ALTER TABLE `history` ADD CONSTRAINT `history_user_id_6457e0b2_fk_users_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);
CREATE INDEX `db_accesses_e8701ad4` ON `db_accesses` (`user_id`);
ALTER TABLE `db_accesses` ADD CONSTRAINT `db_accesses_user_id_08b22a82_fk_users_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);
CREATE INDEX `db_accesses_87ba9b78` ON `db_accesses` (`variants_db_id`);
ALTER TABLE `db_accesses` ADD CONSTRAINT `db_accesses_variants_db_id_a19ceaf1_fk_variants_db_id` FOREIGN KEY (`variants_db_id`) REFERENCES `variants_db` (`id`);
CREATE INDEX `bookmarks_48925eb0` ON `bookmarks` (`db_access_id`);
ALTER TABLE `bookmarks` ADD CONSTRAINT `bookmarks_db_access_id_266c4a03_fk_db_accesses_id` FOREIGN KEY (`db_access_id`) REFERENCES `db_accesses` (`id`);
CREATE INDEX `bam_87ba9b78` ON `bam` (`variants_db_id`);
ALTER TABLE `bam` ADD CONSTRAINT `bam_variants_db_id_69d0f352_fk_variants_db_id` FOREIGN KEY (`variants_db_id`) REFERENCES `variants_db` (`id`);
CREATE INDEX `annotation_87ba9b78` ON `annotation` (`variants_db_id`);
ALTER TABLE `annotation` ADD CONSTRAINT `annotation_variants_db_id_c0a43706_fk_variants_db_id` FOREIGN KEY (`variants_db_id`) REFERENCES `variants_db` (`id`);

COMMIT;
