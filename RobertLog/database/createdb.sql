USE [master]
GO
/****** Object:  Database [robertlog]    Script Date: 2/16/2018 6:10:37 PM ******/
CREATE DATABASE [robertlog]
GO
IF (1 = FULLTEXTSERVICEPROPERTY('IsFullTextInstalled'))
begin
EXEC [robertlog].[dbo].[sp_fulltext_database] @action = 'enable'
end
GO
ALTER DATABASE [robertlog] SET ANSI_NULL_DEFAULT OFF 
GO
ALTER DATABASE [robertlog] SET ANSI_NULLS OFF 
GO
ALTER DATABASE [robertlog] SET ANSI_PADDING OFF 
GO
ALTER DATABASE [robertlog] SET ANSI_WARNINGS OFF 
GO
ALTER DATABASE [robertlog] SET ARITHABORT OFF 
GO
ALTER DATABASE [robertlog] SET AUTO_CLOSE OFF 
GO
ALTER DATABASE [robertlog] SET AUTO_SHRINK OFF 
GO
ALTER DATABASE [robertlog] SET AUTO_UPDATE_STATISTICS ON 
GO
ALTER DATABASE [robertlog] SET CURSOR_CLOSE_ON_COMMIT OFF 
GO
ALTER DATABASE [robertlog] SET CURSOR_DEFAULT  GLOBAL 
GO
ALTER DATABASE [robertlog] SET CONCAT_NULL_YIELDS_NULL OFF 
GO
ALTER DATABASE [robertlog] SET NUMERIC_ROUNDABORT OFF 
GO
ALTER DATABASE [robertlog] SET QUOTED_IDENTIFIER OFF 
GO
ALTER DATABASE [robertlog] SET RECURSIVE_TRIGGERS OFF 
GO
ALTER DATABASE [robertlog] SET  ENABLE_BROKER 
GO
ALTER DATABASE [robertlog] SET AUTO_UPDATE_STATISTICS_ASYNC OFF 
GO
ALTER DATABASE [robertlog] SET DATE_CORRELATION_OPTIMIZATION OFF 
GO
ALTER DATABASE [robertlog] SET TRUSTWORTHY OFF 
GO
ALTER DATABASE [robertlog] SET ALLOW_SNAPSHOT_ISOLATION ON 
GO
ALTER DATABASE [robertlog] SET PARAMETERIZATION SIMPLE 
GO
ALTER DATABASE [robertlog] SET READ_COMMITTED_SNAPSHOT ON 
GO
ALTER DATABASE [robertlog] SET HONOR_BROKER_PRIORITY OFF 
GO
ALTER DATABASE [robertlog] SET RECOVERY FULL 
GO
ALTER DATABASE [robertlog] SET  MULTI_USER 
GO
ALTER DATABASE [robertlog] SET PAGE_VERIFY CHECKSUM  
GO
ALTER DATABASE [robertlog] SET DB_CHAINING OFF 
GO
USE [robertlog]
GO
/****** Object:  User [rluser]    Script Date: 2/16/2018 6:10:37 PM ******/
CREATE USER [rluser] FOR LOGIN [rluser] WITH DEFAULT_SCHEMA=[dbo]
GO
ALTER ROLE [db_datareader] ADD MEMBER [rluser]
GO
ALTER ROLE [db_datawriter] ADD MEMBER [rluser]
GO
/****** Object:  Table [dbo].[Actions]    Script Date: 2/16/2018 6:10:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Actions](
	[ActionID] [bigint] IDENTITY(1,1) NOT NULL,
	[CreateTime] [datetime2](7) NOT NULL,
	[ActionType] [nchar](10) NOT NULL,
	[FromUser] [nvarchar](max) NULL,
	[ActionDetail] [nvarchar](max) NULL,
	[ActionStatus] [nchar](10) NULL
)

GO
/****** Object:  Table [dbo].[RawMsg]    Script Date: 2/16/2018 6:10:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[RawMsg](
	[MsgID] [bigint] IDENTITY(1,1) NOT NULL,
	[TimeStamp] [datetime2](7) NOT NULL,
	[RawMsg] [nvarchar](max) NULL,
	[FromUser] [nvarchar](max) NULL,
	[ToUser] [nvarchar](max) NULL,
	[MsgType] [nvarchar](35) NULL
)

GO
USE [master]
GO
ALTER DATABASE [robertlog] SET  READ_WRITE 
GO

/* create sql in one line
MySQL version
CREATE TABLE [dbo].[Actions](	[ActionID] [bigint] IDENTITY(1,1) NOT NULL,	[CreateTime] [datetime2](7) NOT NULL,	[ActionType] [nchar](10) NOT NULL,	[FromUser] [nvarchar](max) NULL,	[ActionDetail] [nvarchar](max) NULL,	[ActionStatus] [nchar](10) NULL)
CREATE TABLE [dbo].[RawMsg](	[MsgID] [bigint] IDENTITY(1,1) NOT NULL,	[TimeStamp] [datetime2](7) NOT NULL,	[RawMsg] [nvarchar](max) NULL,	[FromUser] [nvarchar](max) NULL,	[ToUser] [nvarchar](10240) NULL,	[MsgType] [nvarchar](35) NULL)

SQLite version:
CREATE TABLE [Actions](	[ActionID] [INTEGER] PRIMARY KEY AUTOINCREMENT,	[CreateTime] [datetime2](7) NOT NULL,	[ActionType] [nchar](10) NOT NULL,	[FromUser] [nvarchar](10240) NULL,	[ActionDetail] [nvarchar](10240) NULL,	[ActionStatus] [nchar](10) NULL)
CREATE TABLE [RawMsg](	[MsgID] [INTEGER] PRIMARY KEY AUTOINCREMENT,	[TimeStamp] [datetime2](7) NOT NULL,	[RawMsg] [nvarchar](10240) NULL,	[FromUser] [nvarchar](10240) NULL,	[ToUser] [nvarchar](10240) NULL,	[MsgType] [nvarchar](35) NULL)
*/