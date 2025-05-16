-- MySQL dump 10.13  Distrib 5.7.44, for Win64 (x86_64)
--
-- Host: sql.didiba.uk    Database: OcrTrade
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
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventory`
--

LOCK TABLES `inventory` WRITE;
/*!40000 ALTER TABLE `inventory` DISABLE KEYS */;
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
-- Table structure for table `nvwa_monitor`
--

DROP TABLE IF EXISTS `nvwa_monitor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nvwa_monitor` (
  `id` int NOT NULL AUTO_INCREMENT,
  `server` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `series` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `price` decimal(18,2) NOT NULL,
  `ma_price` decimal(18,2) NOT NULL,
  `timestamp` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `nvwa_monitor`
--

LOCK TABLES `nvwa_monitor` WRITE;
/*!40000 ALTER TABLE `nvwa_monitor` DISABLE KEYS */;
/*!40000 ALTER TABLE `nvwa_monitor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `operation_logs`
--

DROP TABLE IF EXISTS `operation_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `operation_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operation_type` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `tab_name` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `operation_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `operation_data` text COLLATE utf8mb4_general_ci,
  `reverted` tinyint(1) DEFAULT '0',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `operation_logs`
--

LOCK TABLES `operation_logs` WRITE;
/*!40000 ALTER TABLE `operation_logs` DISABLE KEYS */;
INSERT INTO `operation_logs` VALUES (27,'修改','出库管理','2025-05-14 15:01:34','{\"old\": [\"至纯精华\", \"2025-05-13 15:13:14\", 9, 1188, 535, 10157, \"OCR导入\"], \"new\": [\"至纯精华\", \"2025-05-13 15:13:14\", 10, 1188.0, 535.0, 10157.0, \"OCR导入\"]}',1,'2025-05-14 15:44:49'),(28,'删除','出库管理','2025-05-15 10:01:10','[[\"诛仙古玉\", \"2025-05-15 10:00:49\", 60, 2268, 0, 136080, \"OCR导入\"]]',1,'2025-05-15 10:02:30'),(29,'删除','出库管理','2025-05-15 10:03:43','[[\"诛仙古玉\", \"2025-05-15 10:00:49\", 60, 2268, 0, 136080, \"OCR导入\"]]',1,'2025-05-15 10:04:58'),(30,'删除','出库管理','2025-05-15 10:06:37','[[\"诛仙古玉\", \"2025-05-15 10:00:49\", 60, 2268, 0, 136080, \"OCR导入\"]]',0,'2025-05-15 10:06:37'),(31,'删除','出库管理','2025-05-15 10:09:58','[[\"古玉\", \"2025-05-15 10:09:53\", 60, 2268, 0, 136080, \"OCR导入\"]]',0,'2025-05-15 10:09:58'),(32,'删除','出库管理','2025-05-15 10:10:14','[[\"灵之精火\", \"2025-05-15 10:10:10\", 1, 1269, 64, 1206, \"OCR导入\"]]',0,'2025-05-15 10:10:14'),(33,'删除','入库管理','2025-05-15 10:31:44','[[\"至纯精华\", \"2025-05-15 10:31:36\", 149, 324676, 2179, \"OCR导入\"]]',0,'2025-05-15 10:31:44'),(35,'添加','出库管理','2025-05-15 10:48:55','[{\"item_name\": \"古玉\", \"quantity\": 60, \"unit_price\": 2268, \"fee\": 0, \"deposit\": 0.0, \"total_amount\": 136116, \"note\": \"OCR导入\"}]',0,'2025-05-15 10:48:55'),(36,'删除','出库管理','2025-05-15 10:49:02','[[\"古玉\", \"2025-05-15 10:48:57\", 60, 2268, 0, 136080, \"OCR导入\"]]',0,'2025-05-15 10:49:02'),(37,'添加','交易监控','2025-05-15 11:22:41','[{\"item_name\": \"灵矿髓\", \"quantity\": 3293, \"market_price\": 1947, \"note\": \"OCR导入\"}, {\"item_name\": \"灵草华\", \"quantity\": 8339, \"market_price\": 1095, \"note\": \"OCR导入\"}, {\"item_name\": \"至纯精华\", \"quantity\": 1039, \"market_price\": 1085, \"note\": \"OCR导入\"}, {\"item_name\": \"灵之精火\", \"quantity\": 10330, \"market_price\": 1276, \"note\": \"OCR导入\"}]',0,'2025-05-15 11:22:41'),(38,'修改','出库管理','2025-05-15 11:51:43','{\"old\": [\"灵之精火\", \"2025-05-15 10:48:08\", 77, 1388, 4581, 102295, \"OCR导入\"], \"new\": [\"灵之精火\", \"2025-05-15 10:48:08\", 66, 1388.0, 4581.0, 102295.0, \"OCR导入\"]}',1,'2025-05-15 11:55:44'),(39,'修改','出库管理','2025-05-15 11:57:12','{\"old\": [\"灵之精火\", \"2025-05-15 10:48:08\", 77, 1388, 4581, 102295, \"OCR导入\"], \"new\": [\"灵之精火\", \"2025-05-15 10:48:08\", 66, 1388.0, 4581.0, 102295.0, \"OCR导入\"]}',1,'2025-05-15 11:57:16'),(40,'修改','出库管理','2025-05-15 11:57:25','{\"old\": [\"灵之精火\", \"2025-05-15 10:48:08\", 77, 1388, 4581, 102295, \"OCR导入\"], \"new\": [\"灵之精火\", \"2025-05-15 10:48:08\", 66, 1388.0, 4581.0, 102295.0, \"OCR导入\"]}',0,'2025-05-15 11:57:25'),(41,'修改','入库管理','2025-05-15 11:57:35','{\"old\": [\"灵之精火\", \"2025-05-11 11:17:07\", 999, 88888, 89, \"\"], \"new\": [\"灵之精火\", \"2025-05-11 11:17:07\", 998, 88888.0, 89.0, \"\"]}',1,'2025-05-15 11:57:39'),(42,'添加','出库管理','2025-05-16 11:26:07','[{\"item_name\": \"灵之精火\", \"quantity\": 66, \"unit_price\": 1388, \"fee\": 4581, \"deposit\": 106.0, \"total_amount\": 87133, \"note\": \"OCR导入\"}]',0,'2025-05-16 11:26:07'),(43,'添加','出库管理','2025-05-16 15:20:13','[{\"item_name\": \"古玉\", \"quantity\": 90, \"unit_price\": 2017, \"fee\": 0, \"deposit\": 0.0, \"total_amount\": 181602, \"note\": \"OCR导入\"}, {\"item_name\": \"古玉\", \"quantity\": 71, \"unit_price\": 2017, \"fee\": 0, \"deposit\": 0.0, \"total_amount\": 143263, \"note\": \"OCR导入\"}, {\"item_name\": \"古玉\", \"quantity\": 100, \"unit_price\": 2017, \"fee\": 0, \"deposit\": 0.0, \"total_amount\": 201780, \"note\": \"OCR导入\"}, {\"item_name\": \"古玉\", \"quantity\": 10, \"unit_price\": 2038, \"fee\": 0, \"deposit\": 0.0, \"total_amount\": 20387, \"note\": \"OCR导入\"}, {\"item_name\": \"古玉\", \"quantity\": 6, \"unit_price\": 2038, \"fee\": 0, \"deposit\": 0.0, \"total_amount\": 12232, \"note\": \"OCR导入\"}, {\"item_name\": \"古玉\", \"quantity\": 162, \"unit_price\": 2038, \"fee\": 0, \"deposit\": 0.0, \"total_amount\": 330269, \"note\": \"OCR导入\"}, {\"item_name\": \"古玉\", \"quantity\": 10, \"unit_price\": 2038, \"fee\": 0, \"deposit\": 0.0, \"total_amount\": 20387, \"note\": \"OCR导入\"}, {\"item_name\": \"古玉\", \"quantity\": 63, \"unit_price\": 2038, \"fee\": 0, \"deposit\": 0.0, \"total_amount\": 128438, \"note\": \"OCR导入\"}]',0,'2025-05-16 15:20:13'),(44,'修改','入库管理','2025-05-16 19:15:53','null',0,'2025-05-16 19:15:53'),(45,'修改','入库管理','2025-05-16 19:16:13','null',0,'2025-05-16 19:16:13'),(46,'删除','入库管理','2025-05-16 19:16:50','[[\"古玉\", \"2025-05-16 19:16:12\", 3560, 6052000, 1700, \"\"]]',0,'2025-05-16 19:16:50'),(47,'删除','入库管理','2025-05-16 19:17:01','[[\"古玉\", \"2025-05-16 19:15:52\", 22770, 38709000, 1700, \"\"]]',0,'2025-05-16 19:17:01'),(48,'增加库存','库存管理','2025-05-16 19:29:08','\"物品:灵矿髓,数量:1000,均价:1166\"',0,'2025-05-16 19:29:08'),(49,'增加库存','库存管理','2025-05-16 19:29:08','\"物品:灵矿髓,数量:1000,均价:1166\"',0,'2025-05-16 19:29:08'),(50,'增加库存','库存管理','2025-05-16 19:29:08','\"物品:灵矿髓,数量:1000,均价:1166\"',0,'2025-05-16 19:29:08'),(51,'增加库存','库存管理','2025-05-16 19:29:08','\"物品:灵矿髓,数量:1000,均价:1166\"',0,'2025-05-16 19:29:08'),(52,'增加库存','库存管理','2025-05-16 19:29:08','\"物品:灵矿髓,数量:1000,均价:1166\"',0,'2025-05-16 19:29:08');
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
  `cost` bigint DEFAULT NULL,
  `avg_cost` bigint DEFAULT NULL,
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=102 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_in`
--

LOCK TABLES `stock_in` WRITE;
/*!40000 ALTER TABLE `stock_in` DISABLE KEYS */;
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
  `unit_price` bigint DEFAULT NULL,
  `fee` bigint DEFAULT NULL,
  `deposit` bigint DEFAULT NULL,
  `total_amount` bigint DEFAULT NULL,
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1508 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_out`
--

LOCK TABLES `stock_out` WRITE;
/*!40000 ALTER TABLE `stock_out` DISABLE KEYS */;
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
  `market_price` bigint DEFAULT NULL,
  `target_price` bigint DEFAULT NULL,
  `planned_price` bigint DEFAULT NULL,
  `break_even_price` bigint DEFAULT NULL,
  `profit` bigint DEFAULT NULL,
  `profit_rate` bigint DEFAULT NULL,
  `strategy` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trade_monitor`
--

LOCK TABLES `trade_monitor` WRITE;
/*!40000 ALTER TABLE `trade_monitor` DISABLE KEYS */;
INSERT INTO `trade_monitor` VALUES (15,'至纯精华','2025-05-15 11:22:41',1039,1085,0,0,0,0,0,'','2025-05-13 04:28:19'),(17,'灵矿髓','2025-05-15 11:22:41',3293,1947,0,0,0,0,0,'','2025-05-15 03:17:47'),(18,'灵之精火','2025-05-15 11:22:41',10330,1276,0,0,0,0,0,'','2025-05-15 03:17:53'),(19,'灵草华','2025-05-15 11:22:41',8339,1095,999,0,0,0,0,'','2025-05-15 03:57:56');
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

-- Dump completed on 2025-05-16 19:31:55
