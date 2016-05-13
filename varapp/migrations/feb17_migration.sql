use users_db;

-- Manual
DROP TABLE variants_qc;

-- Django migrations
-- 0002
BEGIN;
-- Create model Annotation
CREATE TABLE `annotation` (`created_at` datetime(6) NULL, `updated_at` datetime(6) NULL, `created_by` varchar(50) NULL, `updated_by` varchar(50) NULL, `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `source` varchar(255) NOT NULL, `annotation` varchar(255) NOT NULL);
-- Create model Bookmarks
CREATE TABLE `bookmarks` (`created_at` datetime(6) NULL, `updated_at` datetime(6) NULL, `created_by` varchar(50) NULL, `updated_by` varchar(50) NULL, `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `query` longtext NOT NULL, `description` varchar(255) NOT NULL, `long_description` longtext NOT NULL, `ip_address` varchar(255) NOT NULL);
-- Remove field bookmarked from history
ALTER TABLE `histories` DROP COLUMN `bookmarked`;
-- Add field query to history
ALTER TABLE `histories` ADD COLUMN `query` longtext NOT NULL;
UPDATE `histories` SET `query` = '';
-- Add field description to preferences
ALTER TABLE `preferences` ADD COLUMN `description` longtext NOT NULL;
UPDATE `preferences` SET `description` = '';
-- Add field preferences to preferences
ALTER TABLE `preferences` ADD COLUMN `preferences` longtext NOT NULL;
UPDATE `preferences` SET `preferences` = '';
-- Add field salt to users
ALTER TABLE `users` ADD COLUMN `salt` varchar(255) DEFAULT '' NOT NULL;
ALTER TABLE `users` ALTER COLUMN `salt` DROP DEFAULT;
-- Add field parent_db_id to variantsdb
ALTER TABLE `variants_db` ADD COLUMN `parent_db_id` integer NULL;
ALTER TABLE `variants_db` ALTER COLUMN `parent_db_id` DROP DEFAULT;
-- Rename table for history to history
RENAME TABLE `histories` TO `history`;
-- Add field user to bookmarks
ALTER TABLE `bookmarks` ADD COLUMN `user_id` integer DEFAULT 1 NOT NULL;
ALTER TABLE `bookmarks` ALTER COLUMN `user_id` DROP DEFAULT;
-- Add field variants_db to bookmarks
ALTER TABLE `bookmarks` ADD COLUMN `variants_db_id` integer NULL;
ALTER TABLE `bookmarks` ALTER COLUMN `variants_db_id` DROP DEFAULT;
-- Add field variants_db to annotation
ALTER TABLE `annotation` ADD COLUMN `variants_db_id` integer DEFAULT 1 NOT NULL;
ALTER TABLE `annotation` ALTER COLUMN `variants_db_id` DROP DEFAULT;
CREATE INDEX `variants_db_fb2b78d2` ON `variants_db` (`parent_db_id`);
ALTER TABLE `variants_db` ADD CONSTRAINT `variants_db_parent_db_id_f334a850_fk_variants_db_id` FOREIGN KEY (`parent_db_id`) REFERENCES `variants_db` (`id`);
CREATE INDEX `bookmarks_e8701ad4` ON `bookmarks` (`user_id`);
ALTER TABLE `bookmarks` ADD CONSTRAINT `bookmarks_user_id_12990ce0_fk_users_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);
CREATE INDEX `bookmarks_87ba9b78` ON `bookmarks` (`variants_db_id`);
ALTER TABLE `bookmarks` ADD CONSTRAINT `bookmarks_variants_db_id_7d875e0f_fk_variants_db_id` FOREIGN KEY (`variants_db_id`) REFERENCES `variants_db` (`id`);
CREATE INDEX `annotation_87ba9b78` ON `annotation` (`variants_db_id`);
ALTER TABLE `annotation` ADD CONSTRAINT `annotation_variants_db_id_c0a43706_fk_variants_db_id` FOREIGN KEY (`variants_db_id`) REFERENCES `variants_db` (`id`);

COMMIT;
-- 0003 was to correct a mistake


-- 0004
-- Remove field ip_address from bookmarks
ALTER TABLE `bookmarks` DROP COLUMN `ip_address`;
-- Add field annotation_version to annotation
ALTER TABLE `annotation` ADD COLUMN `annotation_version` varchar(255) NULL;
ALTER TABLE `annotation` ALTER COLUMN `annotation_version` DROP DEFAULT;
-- Add field source_version to annotation
ALTER TABLE `annotation` ADD COLUMN `source_version` varchar(255) NULL;
ALTER TABLE `annotation` ALTER COLUMN `source_version` DROP DEFAULT;
-- Alter field annotation on annotation
ALTER TABLE `annotation` MODIFY `annotation` longtext NOT NULL;

COMMIT;


-- 0005
BEGIN;
-- Remove field annotation_version from annotation
ALTER TABLE `annotation` DROP COLUMN `annotation_version`;
-- Remove field source_version from annotation
ALTER TABLE `annotation` DROP COLUMN `source_version`;
-- Alter field annotation on annotation
ALTER TABLE `annotation` MODIFY `annotation` varchar(255) NOT NULL;

COMMIT;


-- 0006
BEGIN;
-- Add field annotation_version to annotation
ALTER TABLE `annotation` ADD COLUMN `annotation_version` varchar(255) NULL;
ALTER TABLE `annotation` ALTER COLUMN `annotation_version` DROP DEFAULT;
-- Add field source_version to annotation
ALTER TABLE `annotation` ADD COLUMN `source_version` varchar(255) NULL;
ALTER TABLE `annotation` ALTER COLUMN `source_version` DROP DEFAULT;
-- Alter field annotation on annotation
ALTER TABLE `annotation` MODIFY `annotation` longtext NOT NULL;

COMMIT;


-- 0007
BEGIN;
-- Alter field annotation on annotation
ALTER TABLE `annotation` MODIFY `annotation` varchar(255) NOT NULL;
ALTER TABLE `annotation` MODIFY `annotation` varchar(255) NULL;
-- Alter field source on annotation
ALTER TABLE `annotation` MODIFY `source` varchar(255) NULL;

COMMIT;


-- 0008 
BEGIN;
-- Alter field created_at on annotation
-- Alter field updated_at on annotation
-- Alter field created_at on bookmarks
-- Alter field updated_at on bookmarks
-- Alter field created_at on dbaccess
-- Alter field updated_at on dbaccess
-- Alter field created_at on history
-- Alter field updated_at on history
-- Alter field created_at on people
-- Alter field updated_at on people
-- Alter field created_at on preferences
-- Alter field updated_at on preferences
-- Alter field created_at on roles
-- Alter field updated_at on roles
-- Alter field created_at on users
-- Alter field updated_at on users
-- Alter field created_at on variantsdb
-- Alter field updated_at on variantsdb

COMMIT;


-- Manual: move data from history to bookmarks
INSERT INTO `users_db_bak`.`bookmarks`
	(`id`,
	`user_id`,
	`variants_db_id`,
	`query`,
	`description`,
	`long_description`,
	`created_at`,
	`updated_at`,
	`created_by`,
	`updated_by`
    )
SELECT `history`.`id`,
    `history`.`user_id`,
    `history`.`variants_db_id`,
    `history`.`url`,
    `history`.`description`,
    `history`.`long_description`,
    `history`.`created_at`,
    `history`.`updated_at`,
    `history`.`created_by`,
    `history`.`updated_by`
FROM `users_db_bak`.`history`;


-- Delete what was  bookmarks before. Requires safe mode off
-- DELETE FROM history;


-- Manual: copy what was the settings' secret key into the 'salt' column
UPDATE users SET salt='zwrrj8wmtsd#hv9ru5j+#klm%f*j$@rbdx2z0$&y)(4p(o$s5r';




