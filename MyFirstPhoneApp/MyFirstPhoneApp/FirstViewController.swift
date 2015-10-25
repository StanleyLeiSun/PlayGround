//
//  FirstViewController.swift
//  MyFirstPhoneApp
//
//  Created by Stanley Sun on 15/8/30.
//  Copyright (c) 2015年 Stanley Sun. All rights reserved.
//

import UIKit

class FirstViewController: UIViewController {
    

    override func viewDidLoad() {
        super.viewDidLoad()
        // Do any additional setup after loading the view, typically from a nib.
        
        LoadImgList( "hello");
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
    
    var CurrentImgPairIdx : Int = 0;
    
    func LoadImgList( url:String ) {
        var url = NSURL(string: url)
        //var data = NSData(contentsOfURL: url!)
        var data = NSData(contentsOfFile: "ImgList")
        var str = NSString(data: data!, encoding: NSUTF8StringEncoding)
        
        //var str : NSString = "img1\timg2\r\nimg3\timg4";
        
        var strList = str!.componentsSeparatedByString("\r\n")
        for s in strList
        {
            var imgPair = s.componentsSeparatedByString("\t")
            
            if (imgPair.count != 2)
            {
                continue
            }
            
            self.TopImgList.append(imgPair[0] as! String)
            self.BottomImgList.append(imgPair[1] as! String)
            
        }
        
    }
    
    func MoveToNextLabel() {
        
        if (CurrentImgPairIdx >= TopImgList.count){
            return;//Already done all the cases
        }
        
        TopImg.image = GetImgData(TopImgList[CurrentImgPairIdx]);
        BottomImg.image = GetImgData(BottomImgList[CurrentImgPairIdx]);
        
        CurrentImgPairIdx++;
        
    }
    
    func GetImgData(url:NSString ) -> UIImage? {
        
        var nsd = NSData(contentsOfURL:NSURL(string: url as String )!)
        
        return UIImage(data: nsd!);
    }
    
    
    @IBAction func startGame(){
        let myalert = UIAlertView()
        myalert.title = "准备好了吗"
        //myalert.message = "准备好开始了吗？"
        myalert.addButtonWithTitle("Ready, go!")
        
        var url = NSURL(string: "http://ww2.sinaimg.cn/bmiddle/632dab64jw1ehgcjf2rd5j20ak07w767.jpg" )
        NSLog("Scheme: %@", url!.host!)
        
        var nsd = NSData(contentsOfURL:url!)
        
        var img = UIImage(data: nsd!);
        TopImg.image = img;//  = UIImageView(image: img);
        SecondImg.image = img;
        TopImgName.text = "http://ww2.sinaimg.cn/bmiddle/632dab64jw1ehgcjf2rd5j20ak07w767.jpg" ;
        //vImg.frame.origin = CGPoint(x:0,y:20);
        //self.view.addSubview(vImg);
        
        myalert.show()
    }


}

