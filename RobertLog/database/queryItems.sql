

SELECT top 100 [ActionID]
      ,[CreateTime]
      ,[ActionType]
      ,[FromUser]
      ,[ActionDetail]
      ,[ActionStatus]
  FROM [dbo].[Actions]
  WHERE ActionType = 'WakeUp' or ActionType = 'Sleep' 
  --WHERE CreateTime Between '2018-04-22' And '2018-04-23' 
  order by CreateTime DESC
GO


SELECT top 200 *
  FROM [dbo].RawMsg
  -- WHERE TimeStamp Between '2018-04-22' And '2018-04-24'
  order by TimeStamp DESC
GO