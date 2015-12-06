using Microsoft.WindowsAzure.Storage;
using Microsoft.WindowsAzure.Storage.Table;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Web.Http;

namespace WebApplication.Controllers
{
    public class ImgLabelingController : ApiController
    {
        // GET: api/ImgLabeling
        public IEnumerable<string> Get()
        {
            return new string[] { "LowQualityImage", "BeautifulOnOpal", "ChartImage" };
        }

        // GET: api/ImgLabeling/5
        public List<LabelingTask> Get(string task, int idx)
        {

            switch (task)
            {
                case "LowQualityImage":
                case "BeautifulOnOpal":
                case "ChartImage":
                    {
                        var ret = GetTableContent(task, idx);
                        return ret;
                    }
                default:
                    return null;
            }

        }

        // POST: api/ImgLabeling
        public void Post([FromBody]string value)
        {
            
        }

        // PUT: api/ImgLabeling/5
        //={"task":"testing","instance":"testinginstance","result":"left"}
        public void Put(string id, [FromBody]string value)
        {
            if (!String.IsNullOrWhiteSpace(value))
            {
                dynamic parsedValue = JsonConvert.DeserializeObject<dynamic>(value);
                LabelingResult result = new LabelingResult(
                            (string)parsedValue["task"],
                            (string)parsedValue["instance"],
                            (string)parsedValue["result"]);
                UpdateLabelingResult(result);
            }
            
        }

        // DELETE: api/ImgLabeling/5
        public void Delete(string id)
        {
        }

        CloudStorageAccount account = new CloudStorageAccount(
            new Microsoft.WindowsAzure.Storage.Auth.StorageCredentials(
                "stanleysun",
                "IyqUuwy6iVuXRBZAs3ZTfFDuuZ4PCzk7T3wjr7j9oDlXM43O3i6ip6vqRbN7U2XFc3T3y8EeHMLWeqmTzv7e1Q=="),
            true);
        List<LabelingTask> GetTableContent(string TaskName, int idx)
        {
            CloudTableClient tableClient = account.CreateCloudTableClient();
            CloudTable table = tableClient.GetTableReference("LabelingTask");
            TableQuery<LabelingTask> query = new TableQuery<LabelingTask>()
                .Where(TableQuery.GenerateFilterCondition("PartitionKey", QueryComparisons.Equal, TaskName))
                .Where(TableQuery.GenerateFilterCondition("RowKey", QueryComparisons.Equal, idx.ToString()));

            return table.ExecuteQuery(query).ToList();
        }

        void UpdateLabelingResult(LabelingResult result)
        {
            try
            {
                CloudTableClient tableClient = account.CreateCloudTableClient();
                CloudTable table = tableClient.GetTableReference("LabelingResult");
                var insertOperation = TableOperation.Insert(result);
                table.Execute(insertOperation);
            }
            catch (Exception e)
            { }
        }

        public class LabelingTask : TableEntity
        {
            public string Task { get; set; }
            public string Item { get; set; }

            public string Img1 { get; set; }

            public string Img2 { get; set; }

            public LabelingTask(string t, string i)
            {
                PartitionKey = Task = t;
                RowKey = Item = i;
            }

            public LabelingTask()
            {
                Task = PartitionKey;
                Item = RowKey;
            }

        }
        public class LabelingResult : TableEntity
        {
            public string Task { get; set; }
            public string Instance { get; set; }

            public string Result { get; set; }

            public LabelingResult(string task, string instance, string result)
            {
                PartitionKey = Task = task;
                RowKey = Instance = instance;
                Result = result;
            }

            public LabelingResult() { }
        }
    }
}
