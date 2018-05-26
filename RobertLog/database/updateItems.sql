USE [robertlog]
GO

UPDATE [dbo].[Actions]
   SET [ActionDetail] = N'从18:10到18:40，睡了0小时30分钟', ActionStatus = N'Active', CreateTime = N'2018-05-08 18:40:00.0000000'
 WHERE ActionID = 2699
GO

UPDATE [dbo].[Actions]
   SET [ActionDetail] = N'奶瓶:10mL'
 WHERE ActionID = 2798
GO

UPDATE dbo.Actions set ActionStatus = N'Deleted'
where ActionID = 2259

INSERT INTO dbo.Actions VALUES ("2018-05-21 7:15:00.0", 'WakeUp', 'ocgSc0cpvPB5V7KPdcBSdu0VQvXQ', '从14:11到17:00，睡了2小时49分钟', 'Active' ) 