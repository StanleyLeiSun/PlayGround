//
//  GlobalSetting.swift
//  MyFirstPhoneApp
//
//  Created by Stanley Sun on 15/11/29.
//  Copyright © 2015年 Stanley Sun. All rights reserved.
//

import Foundation

public class GlobalSetting{
    public static var CurTask : String = "LowQuality";
    public static var CurItemIdx : Int = 0;
    public static var CurImageSize : String = "120x80"//"1024x1024";//"80x80"
    
    public static var ImgSizes = ["80x80", "120x80", "1024x1024"]
    
    public static var TaskList = [ "LowQualityImage", "BeautifulOnOpal", "ChartImage"];
    
    public static let ServiceAddr : String = "https://stanleysun.azurewebsites.net/api/ImgLabeling";
    public static func RefreshTasks()
    {//Get task list from
        let url = NSURL(string:ServiceAddr)
        
        do{
            //var webResult = try NSString(contentsOfURL: url!, encoding: NSUTF8StringEncoding);
            
            let jsonData = NSData(contentsOfURL: url!);
            let json  =  try! NSJSONSerialization.JSONObjectWithData(jsonData!, options:NSJSONReadingOptions.AllowFragments)
            
            let tasks = json as! NSArray;
            TaskList.removeAll();
            for i in tasks
            {
                TaskList.append(i as! String);
            }
            //var tasks = webResult.substringToIndex(2);
            
        }catch {}
        
        CurTask = TaskList[0];
        
    }
}