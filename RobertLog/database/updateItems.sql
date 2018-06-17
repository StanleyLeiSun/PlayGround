USE [robertlog]
GO

UPDATE [dbo].[Actions]
   SET [ActionDetail] = N'从9:40到4:40，睡了7小时0分钟', ActionStatus = N'Active', CreateTime = N'2018-05-27 4:40:00.0000000'
 WHERE ActionID = 3176
GO

UPDATE [dbo].[Actions]
   SET [ActionDetail] = N'奶瓶:10mL'
 WHERE ActionID = 2798
GO

UPDATE dbo.Actions set ActionStatus = N'Deleted'
where ActionID = 2259

update Actions set ActionDetail = N'从12:25到14:44，睡了2小时19分' where ActionID = 3661
 
INSERT INTO dbo.Actions VALUES ('2018-05-27 4:40:00.0', 'WakeUp', 'ocgSc0cpvPB5V7KPdcBSdu0VQvXQ', N'从9:40到4:40，睡了7小时0分钟', 'Active' ) 

INSERT INTO Actions VALUES('2018-06-15T07:58:00.0000000', 'Feed', 'ocgSc0eChTDEABMBHJ_urv4lMeCE',N'喂奶：120mL','Active')