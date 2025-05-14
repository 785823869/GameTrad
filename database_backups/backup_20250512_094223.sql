-- MySQL dump 10.13  Distrib 5.7.44, for Win64 (x86_64)
--
-- Host: 192.168.3.22    Database: OcrTrade
-- ------------------------------------------------------
-- Server version	8.4.5

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `inventory`
--

DROP TABLE IF EXISTS `inventory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `inventory` (
  `id` int NOT NULL AUTO_INCREMENT,
  `item_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `quantity` int NOT NULL DEFAULT '0',
  `avg_price` decimal(10,2) NOT NULL DEFAULT '0.00',
  `break_even_price` decimal(10,2) NOT NULL DEFAULT '0.00',
  `selling_price` decimal(10,2) NOT NULL DEFAULT '0.00',
  `profit` decimal(10,2) NOT NULL DEFAULT '0.00',
  `profit_rate` decimal(5,2) NOT NULL DEFAULT '0.00',
  `total_profit` decimal(10,2) NOT NULL DEFAULT '0.00',
  `inventory_value` decimal(10,2) NOT NULL DEFAULT '0.00',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventory`
--

LOCK TABLES `inventory` WRITE;
/*!40000 ALTER TABLE `inventory` DISABLE KEYS */;
INSERT INTO `inventory` VALUES (1,'的撒旦',0,0.00,0.00,0.00,0.00,0.00,0.00,0.00,'2025-05-10 09:19:51','2025-05-10 09:19:51'),(2,'而我却',0,0.00,0.00,0.00,0.00,0.00,0.00,0.00,'2025-05-10 09:31:17','2025-05-10 09:31:17'),(3,'玩玩',0,0.00,0.00,0.00,0.00,0.00,0.00,0.00,'2025-05-10 09:48:38','2025-05-10 09:49:01'),(4,'至纯精华',0,0.00,0.00,0.00,0.00,0.00,0.00,0.00,'2025-05-10 10:46:33','2025-05-10 23:14:44'),(5,'大苏打',0,0.00,0.00,0.00,0.00,0.00,0.00,0.00,'2025-05-10 17:56:23','2025-05-10 17:56:23'),(6,'至纯精华',298,2179.00,2179.00,0.00,0.00,-100.00,0.00,649352.00,'2025-05-11 06:25:15','2025-05-11 06:25:15'),(7,'玩玩',11,5050.00,5050.00,0.00,0.00,-100.00,0.00,55555.00,'2025-05-11 06:25:15','2025-05-11 06:25:15');
/*!40000 ALTER TABLE `inventory` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `item_dict`
--

DROP TABLE IF EXISTS `item_dict`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `item_dict` (
  `id` int NOT NULL AUTO_INCREMENT,
  `item_name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `item_name` (`item_name`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `item_dict`
--

LOCK TABLES `item_dict` WRITE;
/*!40000 ALTER TABLE `item_dict` DISABLE KEYS */;
INSERT INTO `item_dict` VALUES (1,'物品1','默认物品1描述'),(2,'物品2','默认物品2描述');
/*!40000 ALTER TABLE `item_dict` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `operation_logs`
--

DROP TABLE IF EXISTS `operation_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `operation_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `op_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `tab_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `data` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `timestamp` datetime DEFAULT CURRENT_TIMESTAMP,
  `reverted` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `operation_logs`
--

LOCK TABLES `operation_logs` WRITE;
/*!40000 ALTER TABLE `operation_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `operation_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `silver_monitor`
--

DROP TABLE IF EXISTS `silver_monitor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `silver_monitor` (
  `id` int NOT NULL AUTO_INCREMENT,
  `server` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `series` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `price` decimal(10,4) DEFAULT NULL,
  `ma_price` decimal(10,4) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_silver` (`server`,`series`,`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `silver_monitor`
--

LOCK TABLES `silver_monitor` WRITE;
/*!40000 ALTER TABLE `silver_monitor` DISABLE KEYS */;
/*!40000 ALTER TABLE `silver_monitor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stock_in`
--

DROP TABLE IF EXISTS `stock_in`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `stock_in` (
  `id` int NOT NULL AUTO_INCREMENT,
  `item_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `transaction_time` datetime NOT NULL,
  `quantity` int NOT NULL,
  `cost` decimal(10,2) NOT NULL,
  `avg_cost` decimal(10,2) NOT NULL,
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_in`
--

LOCK TABLES `stock_in` WRITE;
/*!40000 ALTER TABLE `stock_in` DISABLE KEYS */;
INSERT INTO `stock_in` VALUES (5,'玩玩','2025-05-10 17:48:38',11,55555.00,5050.45,'','2025-05-10 09:48:38'),(17,'至纯精华','2025-05-11 01:49:39',149,324676.00,2179.03,'OCR导入','2025-05-10 17:49:39'),(20,'至纯精华','2025-05-11 07:14:44',149,324676.00,2179.03,'OCR导入','2025-05-10 23:14:44'),(21,'灵之精火','2025-05-11 11:17:07',999,88888.00,88.98,'','2025-05-11 03:17:07');
/*!40000 ALTER TABLE `stock_in` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stock_out`
--

DROP TABLE IF EXISTS `stock_out`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `stock_out` (
  `id` int NOT NULL AUTO_INCREMENT,
  `item_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `transaction_time` datetime NOT NULL,
  `quantity` int NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  `fee` decimal(10,2) NOT NULL,
  `deposit` decimal(10,2) NOT NULL DEFAULT '0.00',
  `total_amount` decimal(10,2) NOT NULL,
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_out`
--

LOCK TABLES `stock_out` WRITE;
/*!40000 ALTER TABLE `stock_out` DISABLE KEYS */;
INSERT INTO `stock_out` VALUES (3,'灵之精火','2025-05-11 12:50:31',66,1388.00,4581.00,0.00,87027.00,'OCR导入','2025-05-11 04:50:31'),(4,'灵之精火','2025-05-11 13:06:24',66,1388.00,4581.00,0.00,87027.00,'OCR导入','2025-05-11 05:06:24'),(5,'灵之精火','2025-05-11 13:06:24',66,1388.00,4581.00,0.00,87027.00,'OCR导入','2025-05-11 06:25:15'),(6,'灵之精火','2025-05-11 12:50:31',66,1388.00,4581.00,0.00,87027.00,'OCR导入','2025-05-11 06:25:15');
/*!40000 ALTER TABLE `stock_out` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trade_monitor`
--

DROP TABLE IF EXISTS `trade_monitor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trade_monitor` (
  `id` int NOT NULL AUTO_INCREMENT,
  `item_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `monitor_time` datetime NOT NULL,
  `quantity` int NOT NULL,
  `market_price` decimal(10,2) NOT NULL,
  `target_price` decimal(10,2) NOT NULL,
  `planned_price` decimal(10,2) NOT NULL,
  `break_even_price` decimal(10,2) NOT NULL,
  `profit` decimal(10,2) NOT NULL,
  `profit_rate` decimal(5,2) NOT NULL,
  `strategy` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trade_monitor`
--

LOCK TABLES `trade_monitor` WRITE;
/*!40000 ALTER TABLE `trade_monitor` DISABLE KEYS */;
INSERT INTO `trade_monitor` VALUES (1,'灵矿髓','2025-05-11 16:25:00',3293,1947.00,0.00,0.00,0.00,0.00,0.00,'','2025-05-11 08:25:00'),(2,'灵草华','2025-05-11 16:25:01',8339,1095.00,0.00,0.00,0.00,0.00,0.00,'','2025-05-11 08:25:01'),(3,'至纯精华','2025-05-11 16:25:01',1039,1085.00,0.00,0.00,0.00,0.00,0.00,'','2025-05-11 08:25:01'),(4,'灵之精火','2025-05-11 16:25:01',10330,1276.00,0.00,0.00,0.00,0.00,0.00,'','2025-05-11 08:25:01');
/*!40000 ALTER TABLE `trade_monitor` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-05-12  9:42:23
