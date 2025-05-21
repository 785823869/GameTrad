-- Create the transactions table for the OcrTrade database
-- This fixes the "Table 'OcrTrade.transactions' doesn't exist" error

CREATE TABLE IF NOT EXISTS `transactions` (
    `id` int NOT NULL AUTO_INCREMENT,
    `transaction_type` VARCHAR(50) NOT NULL,
    `transaction_time` DATETIME NOT NULL,
    `item_name` VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    `quantity` INT NOT NULL,
    `price` DECIMAL(10,2) NOT NULL,
    `total_amount` DECIMAL(10,2) NOT NULL,
    `fee` DECIMAL(10,2) DEFAULT 0,
    `platform` VARCHAR(50) DEFAULT '',
    `note` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    `target_price` DECIMAL(10,2) DEFAULT 0,
    `planned_price` DECIMAL(10,2) DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add useful indexes
CREATE INDEX idx_transaction_type ON transactions (transaction_type);
CREATE INDEX idx_transaction_time ON transactions (transaction_time);
CREATE INDEX idx_item_name ON transactions (item_name); 