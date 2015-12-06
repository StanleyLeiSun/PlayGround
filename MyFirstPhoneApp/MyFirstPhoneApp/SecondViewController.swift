//
//  SecondViewController.swift
//  MyFirstPhoneApp
//
//  Created by Stanley Sun on 15/8/30.
//  Copyright (c) 2015年 Stanley Sun. All rights reserved.
//

import UIKit

class LabelingTask{
    var TaskID : String = "";
    
    var TaskName : String = "";
    
    var ImageSize : [String] = [];
}

class SecondViewController: UIViewController, UIPickerViewDataSource, UIPickerViewDelegate {

    override func viewDidLoad() {
        super.viewDidLoad()
        loadTasks("abc")
        // Do any additional setup after loading the view, typically from a nib.
    }
    
    override func viewDidDisappear(animated: Bool) {
        if ( selectedTask != -1 && GlobalSetting.TaskList[selectedTask] != GlobalSetting.CurTask)
        {
            GlobalSetting.CurTask = GlobalSetting.TaskList[selectedTask];
            GlobalSetting.CurItemIdx = 0;
        }
        
        GlobalSetting.CurImageSize = GlobalSetting.ImgSizes[selectedSize];
    }
    

    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
        // Dispose of any resources that can be recreated.
    }
    
    
    func loadTasks( srvAddress : String){
    
        //var url = NSURL(string:srvAddress)
        
        //var data = NSData(contentsOfURL: url!
        //_ = NSInputStream(fileAtPath : "/Users/stanleysun/Documents/Projects/PlayGround/PlayGround/MyFirstPhoneApp/MyFirstPhoneApp/TaskList")
        let TaskFilePath : NSString = "/Users/stanleysun/Documents/Projects/PlayGround/PlayGround/MyFirstPhoneApp/MyFirstPhoneApp/TaskList2"
        
        //let JsonData = NSData.dataWithContentsOfFile(TaskFilePath, options: DataReadingMappedIfSafe, error: nil)
        
        var text2 : NSString
        //var s:String =  as String;
        do{
         let JsonData = NSData(contentsOfFile: TaskFilePath as String)
         //text2 = try NSString(contentsOfFile: TaskFilePath as String, encoding: NSUTF8StringEncoding)
            
         //let json  =  try! NSJSONSerialization.JSONObjectWithData(JsonData!,options:NSJSONReadingOptions.AllowFragments)
            
        }catch{}
        

        //for i in json.objectForKey("result") as! NSArray
        //{
            //var t : LabelingTask;
            //t.TaskID = i.objectForKey("TaskID")
            //t.TaskName = i.objectForKey("TaskName")
            //t.ImageSize = i.objectForKey("ImageSize")
        //}

    }
    
    func numberOfComponentsInPickerView(pickerView: UIPickerView) -> Int {
        return 2
    }
    
    func pickerView(pickerView: UIPickerView, numberOfRowsInComponent component: Int)->Int {
        
        switch (component)
        {
        case 0 : return GlobalSetting.TaskList.count;
        case 1: return GlobalSetting.ImgSizes.count;
        default:
            return 0;
        }
    }
    
    func pickerView(pickerView: UIPickerView, titleForRow row: Int, forComponent component: Int) -> String? {
        
        switch (component)
        {
        case 0 : return GlobalSetting.TaskList[row];
        case 1: return GlobalSetting.ImgSizes[row];
        default: return "Invalid";
        }
    }
    
    var selectedTask : NSInteger = -1;
    var selectedSize : NSInteger = 0;
    func pickerView(pickerView: UIPickerView, didSelectRow row: Int, inComponent component: Int){
        switch (component)
        {
        case 0 : selectedTask = row; break;
        case 1: selectedSize = row; break;
        default: break
        }
    }




}

