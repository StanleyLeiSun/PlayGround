USE [robertlog]
GO

SELECT top 100 [ActionID]
      ,[CreateTime]
      ,[ActionType]
      ,[FromUser]
      ,[ActionDetail]
      ,[ActionStatus]
  FROM [dbo].[Actions]
  --WHERE ActionType = 'WakeUp' or ActionType = 'Sleep' 
  --WHERE CreateTime Between '2018-04-22' And '2018-04-23' 
  order by CreateTime DESC
GO


SELECT top 200 *
  FROM [dbo].RawMsg
  WHERE TimeStamp Between '2018-04-22' And '2018-04-24'
  order by TimeStamp DESC
GO

UPDATE [dbo].[Actions]
   SET [ActionDetail] = N'?22:00?05:48,??7??48??', ActionStatus = N'Active'
 WHERE ActionID = 2706
GO