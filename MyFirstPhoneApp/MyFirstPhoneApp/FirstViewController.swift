//
//  FirstViewController.swift
//  MyFirstPhoneApp
//
//  Created by Stanley Sun on 15/8/30.
//  Copyright (c) 2015年 Stanley Sun. All rights reserved.
//

import UIKit

class FirstViewController: UIViewController {
    
    var THParameter = "&w=80&h=80&c=7";
    
    override func viewDidLoad() {
        super.viewDidLoad()
        // Do any additional setup after loading the view, typically from a nib.
        
        GlobalSetting.RefreshTasks();
        SetImgSize();
        
        LoadImgList();
        
        MoveToNextLabel()
    }
    @IBOutlet weak var TopImg: UIImageView!

    @IBOutlet weak var BottomImgName: UILabel!
    @IBOutlet weak var BottomImg: UIImageView!
    @IBOutlet weak var TopImgName: UILabel!
    
    @IBOutlet weak var SecondImg: UIImageView!
    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
        // Dispose of any resources that can be recreated.
    }
    
    //ImgData
    var TopImgList : [String] = [];
    var BottomImgList : [String] = [];
    var LabelResult : [Int] = [];
    
    var CurrentImgPairIdx : Int = 0;
    
    func SetImgSize(){
        //Prepare th parameter
        var w :Int = 0;
        var h : Int = 0;
        switch GlobalSetting.CurImageSize
        {
        case "80x80": w = 80;  h = 80; break;
        case "1024x1024": w = 1024; h = 1024; break;
        case "120x80" : w = 120; h = 80; break;
        default: break;
        }
        THParameter = String(format: "&w=%d&h=%d&c=7&pid=popnow&pid=popnow", w,h);
        //Reset the layout

        //TopImg.bounds.size.width = CGFloat(w);
        //TopImg.bounds.size.height = CGFloat(h);
        //TopImg.frame.size.width = CGFloat(w);
        //TopImg.frame.size.height = CGFloat(w);
        

        //BottomImg.bounds.size.width = CGFloat(w);
        //BottomImg.bounds.size.height = CGFloat(h);

    }
    
    func LoadImgList() {
        
        //var url = NSURL(string: url)
        //var data = NSData(contentsOfURL: url!)
        let data = NSData(contentsOfFile: "/Users/stanleysun/Documents/Projects/PlayGround/PlayGround/MyFirstPhoneApp/MyFirstPhoneApp/ImgList")
        let str = NSString(data: data!, encoding: NSUTF8StringEncoding)
        
        //var str : NSString = "img1\timg2\r\nimg3\timg4";
        
        let strList = str!.componentsSeparatedByString("\r\n")
        for s in strList
        {
            var imgPair = s.componentsSeparatedByString(" ")
            
            if (imgPair.count != 2)
            {
                continue
            }
            
            self.TopImgList.append(imgPair[0] + THParameter)
            self.BottomImgList.append(imgPair[1] + THParameter)
            
        }
        
    }
    
    func MoveToNextLabel() {
        
        if (CurrentImgPairIdx >= TopImgList.count){
            return;//Already done all the cases
        }
        
        //NSString.
        let url : NSURL = NSURL(string:
            String(format:"%@?task=%@&idx=%d",
                GlobalSetting.ServiceAddr,
                GlobalSetting.CurTask,
                CurrentImgPairIdx+1))!;
        
        //var webResult = try NSString(contentsOfURL: url!, encoding: NSUTF8StringEncoding);
        //var tasks = webResult.substringToIndex(2);
        let jsonData = NSData(contentsOfURL: url)
        let json  =  try! NSJSONSerialization.JSONObjectWithData(jsonData!, options:NSJSONReadingOptions.AllowFragments)
        
        
        
        TopImg.image = GetImgData(TopImgList[CurrentImgPairIdx]);
        SecondImg.image = GetImgData(BottomImgList[CurrentImgPairIdx]);
        
        CurrentImgPairIdx++;
        
    }
    
    func GetImgData(url:NSString ) -> UIImage? {
        
        let nsd = NSData(contentsOfURL:NSURL(string: url as String )!)
        
        if (nsd == nil)
        {
            return nil;
        }
        return UIImage(data: nsd!);
    }
    
    //1: top 2: Bottom 3: OnPar
    @IBAction func TopBetter(){
        
        LabelResult.append(1)
        MoveToNextLabel()
    }
    
    @IBAction func BottomBetter(){
        
        LabelResult.append(2)
        MoveToNextLabel()
    }
    
    @IBAction func Skip(){
        
        LabelResult.append(3)
        MoveToNextLabel()
    }
    
    @IBAction func Skip2(){
        
        LabelResult.append(3)
        MoveToNextLabel()
    }
    

}

