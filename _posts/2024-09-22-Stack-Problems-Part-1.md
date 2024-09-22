---
layout: post
title: Stack Problems - Part I
published: true
---

This wiki contains a couple of well-defined problems on Stack.


### Exam Progress (3544):

Given a non-empty integer array nums representing the student's scores for each test, return an equal-length array res, and for each test score nums[i] in nums, find the nearest higher score after it, or keep the original test score if the nearest higher score does not exist.

```cpp
    vector<int> getProgress(vector<int> &nums) {
        // write your code 
        vector<int> nearHighNumbers(nums.size());
        list<int> rightNearestHigh;
        for(int i=nums.size()-1;i>=0;i--){
            while(rightNearestHigh.size()>0 && nums[i]>=nums[rightNearestHigh.back()]){
                rightNearestHigh.pop_back();
            }
            if(rightNearestHigh.size()==0){
                nearHighNumbers[i] = nums[i];
            } else {
                nearHighNumbers[i] = nums[rightNearestHigh.back()];
            }
            rightNearestHigh.push_back(i);
        }
        return nearHighNumbers;
    }
```



### N-ary Tree Postorder Traversal (1525):

Given an n-ary tree, return the postorder traversal of its nodes' values.

```cpp
    vector<int> postorder(UndirectedGraphNode *root) {
        // write your code here
        vector<int> traversal;
        list<UndirectedGraphNode*> stck1, stck2;
        if(root){
            stck1.push_back(root);
        }
        while(stck1.size()>0){
            UndirectedGraphNode* node = stck1.back();
            stck1.pop_back();
            stck2.push_back(node);
            for(int i=0;i<node->neighbors.size();i++){
                stck1.push_back(node->neighbors[i]);
            }
        }
        while(stck2.size()>0){
            traversal.push_back(stck2.back()->label);
            stck2.pop_back();
        }
        return traversal;
    }
```




### N-ary Tree Preorder Traversal (1526):

Given an n-ary tree, return the preorder traversal of its nodes' values.

```cpp
    vector<int> preorder(UndirectedGraphNode *root) {
        // write your code here
        vector<int> traversal;
        list<UndirectedGraphNode*> stck;
        if(root){
            stck.push_back(root);
        }
        while(stck.size()>0){
            UndirectedGraphNode* node = stck.back();
            stck.pop_back();
            traversal.push_back(node->label);
            for(int i=node->neighbors.size()-1;i>=0;i--){
                stck.push_back(node->neighbors[i]);
            }
        }
        return traversal;
    }
```



### Longest Valid Parentheses (193):

Given a string containing just the characters '(' and ')', find the length of the longest valid (well-formed) parentheses substring.

```cpp
    int longestValidParentheses(string &s) {
        // write your code here
        list<pair<char,int>> paren;
        for(int i=0;i<s.size();i++){
            char ch = s[i];
            if(ch=='('){
                paren.push_back(make_pair(ch,i));
            } else if(ch==')'){
                if(paren.size()>0 && paren.back().first=='('){
                    paren.pop_back();
                } else {
                    paren.push_back(make_pair(ch, i));
                }
            }
        }
        paren.push_back(make_pair('-',s.size()));

        int startIndex = -1, maxLen=0;
        for(const auto &p: paren){
            cout<<"start:"<<startIndex<<" curr:"<<p.second<<endl;
            int len = p.second - startIndex -1;
            maxLen = max(maxLen, len);
            startIndex = p.second;
        }
        return maxLen;
    }
```



### Trapping Rain Water (363):

Given n non-negative integers representing an elevation map where the width of each bar is 1, compute how much water it is able to trap after raining.

```cpp
    int trapRainWater(vector<int> &heights) {
        // write your code here
        vector<int> maxLeftHeights(heights.size()), maxRightHeights(heights.size());
        for(int i=0;i<heights.size();i++){
            if(i==0){
                maxLeftHeights[i] = i;
            } else {
                if (heights[maxLeftHeights[i-1]] > heights[i]){
                    maxLeftHeights[i] = maxLeftHeights[i-1];
                } else {
                    maxLeftHeights[i] = i;
                }
            }
        }

        for(int i=heights.size()-1;i>=0;i--){
            if(i==heights.size()-1){
                maxRightHeights[i] = i;
            } else {
                if(heights[maxRightHeights[i+1]] > heights[i]){
                    maxRightHeights[i] = maxRightHeights[i+1];
                } else {
                    maxRightHeights[i] = i;
                }
            }
        }

        int trappedWaterAmount = 0;
        for(int i=0;i<heights.size();i++){
            cout<<"i:"<<i<<" leftIndex:"<<maxLeftHeights[i]<<" rightIndex:"<<maxRightHeights[i]<<endl;
            trappedWaterAmount += min(heights[maxLeftHeights[i]], heights[maxRightHeights[i]])-heights[i];
        }
        return trappedWaterAmount;
    }
```



### Simplify Path (421):

Given an absolute path for a file (Unix-style), simplify it.

In a UNIX-style file system, a period . refers to the current directory. Furthermore, a double period .. moves the directory up a level.

The result must always begin with /, and there must be only a single / between two directory names. The last directory name (if it exists) must not end with a trailing /. Also, the result must be the shortest string representing the absolute path.


```cpp
    string simplifyPath(string &path) {
        // write your code here
        string currStr = "";
        list<string> stck;
        path += "/";
        for(int i=0;i<path.size();i++){
            char ch = path[i];
            if(ch=='/'){
                if(currStr==".." && stck.size()>0){
                    // cout<<"pop:"<<stck.back()<<endl;
                    stck.pop_back();
                } else if(currStr!=".." && currStr!="." && currStr!=""){
                    // cout<<"insert:"<<currStr<<endl;
                    stck.push_back(currStr);
                }
                currStr = "";
            } else {
                currStr += ch;
            }
            // cout<<"i:"<<i<<" ch:"<<ch<<" str:"<<currStr<<endl;
        }

        string result = "";
        for(const auto &elem : stck){
            result += "/"+elem;
        }
        return result.size()==0?"/":result;
    }
```



### Asteroid Collision (1001):

Given an array of integers representing asteroids in a row. For each asteroid, the absolute value represents its size, and the sign represents its direction (positive meaning right, negative meaning left). Each asteroid moves at the same speed.

Find out the state of the asteroids after all collisions. If two asteroids meet, the smaller one will explode. If both are the same size, both will explode. Two asteroids moving in the same direction will never meet.

```cpp
    vector<int> asteroidCollision(vector<int> &asteroids) {
        // write your code here
        list<int> stck;
        bool sameSizeColl = false;
        for(int i=0;i<asteroids.size();i++){
            cout<<"index:"<<i;
            while(stck.size()>0 && abs(asteroids[i])>= abs(asteroids[stck.back()]) && 
                (
                    //(asteroids[i]>0 && abs(asteroids[stck.back()]<0)) || 
                    (asteroids[i]<0 && abs(asteroids[stck.back()]>0))
            )){
                cout<<" pop:"<<stck.back();
                stck.pop_back();
                if(abs(asteroids[i])>= abs(asteroids[stck.back()])){
                    sameSizeColl =  true;
                }
            }

            if (stck.size()>0 && abs(asteroids[i]) <= abs(asteroids[stck.back()]) && 
                (
                    //(asteroids[i]>0 && abs(asteroids[stck.back()]<0)) || 
                    (asteroids[i]<0 && abs(asteroids[stck.back()]>0))
            )){
                // asteroid is gone
            } else if(!sameSizeColl) {
                cout<<" push:"<<i;
                stck.push_back(i);
            }
            cout<<endl;
        }
        vector<int> result;
        for(const auto &elem : stck){
            result.push_back(asteroids[elem]);
        }
        return result;
    }
```



### Final Discounted Price (1852):

A shopkeeper needs to complete a sales task. He arranges the items for sale in a row.
Starting from the left, the shopkeeper subtracts the price of the first lower or the same price item on the right side of the item from its full price.
If there is no item to the right that costs less than or equal to the current item's price, the current item is sold at full price.
You should return the actual selling price of each item. (nearest smaller)

```cpp
    vector<int> finalDiscountedPrice(vector<int> &prices) {
        // write your code here
        list<int> stck;
        vector<int> result(prices.size());
        for(int i=prices.size()-1;i>=0;i--){
            while(stck.size()>0 && prices[i]<prices[stck.back()]){
                stck.pop_back();
            }
            if(stck.size()==0){
                result[i] = prices[i];
            } else {
                result[i] = prices[i]-prices[stck.back()];
            }
            stck.push_back(i);
        }
        return result;
    }
```



### Online Stock Span (1740):

Write a class StockSpanner which collects daily price quotes for some stock, and returns the span of that stock's price for the current day.

The span of the stock's price today is defined as the maximum number of consecutive days (starting from today and going backwards) for which the price of the stock was less than or equal to today's price.

For example, if the price of a stock over the next 7 days were [100, 80, 60, 70, 60, 75, 85], then the stock spans would be [1, 1, 1, 2, 1, 4, 6].

```cpp
    int next(int price) {
        // Write your code here.
        vector<int> prices;
        list<int> stck;
        while(stck.size()>0 && price>=prices[stck.back()]){
            stck.pop_back();
        }
        int retValue = 0;
        if(stck.size()==0){
            retValue = prices.size()+1;
        }else{
            retValue = prices.size()-stck.back();
        }
        prices.push_back(price);
        stck.push_back(prices.size()-1);
        return retValue;
    }
```



### Remove Repeated Letters (3599):

Given a string s, remove the duplicate letters in the string so that the letters present in the string appear only once, and return the result with the smallest dictionary order without disrupting the relative positions of the letters in the original string.


```cpp
    string removeDuplicateLetters(string &s) {
        // write your code here
        map<char,int> finalIndexMapper;
        for(int i=0;i<s.size();i++){
            char ch = s[i];
            finalIndexMapper[ch] = i;
        }

        set<char> visited;
        list<int> stck;
        for(int i=0;i<s.size();i++){
            char ch = s[i];
            if(visited.find(s[i]) == visited.end()){
                while(stck.size()>0 && ch<s[stck.back()] && i<finalIndexMapper[s[stck.back()]]){
                    visited.erase(s[stck.back()]);
                    stck.pop_back();
                }
                visited.insert(s[i]);
                stck.push_back(i);
            }
        }

        string result = "";
        for(const auto &elem : stck){
            result += s[elem];
        }
        return result;
    }
```



### Parentheses Score (268):

Given a balanced parentheses string S, compute the score of the string based on the following rule:
- () has score 1
- AB has score A + B, where A and B are balanced parentheses strings.
- (A) has score 2 * A, where A is a balanced parentheses string.


```cpp
    int parenthesesScore(string &s) {
        // write your code here
        s = '('+s+')';
        list<pair<char,int>> stck;
        for(int i=0;i<s.size();i++){
            char ch = s[i];
            if(ch=='('){
                stck.push_back(make_pair(ch,0));
            } else { // balanced parenthesis
                pair<char,int> pr = stck.back();
                stck.pop_back();
                int score = pr.second==0?1:2*pr.second;
                if(stck.size()==0){
                    return score/2;
                } else {
                    stck.back().second += score;
                }
            }
        }
        return -1;// case of imbalanced parenthesis
    }
```



###  Convert Expression to Reverse Polish Notation (370):

Given a string array representing an expression, and return the Reverse Polish notation of this expression. (remove the parentheses)

```cpp
    vector<string> convertToRPN(vector<string> &expression) {
        // write your code here

        map<string,int> precedenceMapper;
        precedenceMapper["("] = 3;
        precedenceMapper["/"] = 2;
        precedenceMapper["*"] = 2;
        precedenceMapper["-"] = 1;
        precedenceMapper["+"] = 1;

        vector<string> postFix;
        list<string> stck;
        for(int i=0;i<expression.size();i++){
            string element = expression[i];
            if(element=="("){
                stck.push_back("(");
            } else if(element==")"){
                while(stck.size()>0 && stck.back()!="("){
                    postFix.push_back(stck.back());
                    cout<<"sc 1 pop:"<<stck.back()<<endl;
                    stck.pop_back();
                }
                // assert stck.size()>0 && stck.back()=="("
                cout<<"sc 2 pop:"<<stck.back()<<endl;
                stck.pop_back();
            } else if(precedenceMapper.find(element) == precedenceMapper.end()){
                // operand
                postFix.push_back(element);
            } else {
                if(stck.size()>0 && precedenceMapper[element]>=precedenceMapper[stck.back()]){
                    // complete the operation first
                    postFix.push_back(stck.back());
                    cout<<"sc 3 pop:"<<stck.back()<<endl;
                    stck.pop_back();
                }
                stck.push_back(element);
                cout<<"sc 4 push:"<<stck.back()<<endl;
            }
        }
        while(stck.size()>0){
            postFix.push_back(stck.back());
            stck.pop_back();
        }
        return postFix;
    }
```




### Prefix notation to postfix notation (271):

Transform a prefix natation to a postfix notation.

```cpp
    string prefixNotationToPostfixNotation(string &str) {
        // write your code here.
        vector<string> arr;

        // convert str to array of operations
        string currStr = "";
        for(int i=0;i<str.size();i++){
            if(str[i]==' '){
                if(currStr!=""){
                    arr.push_back(currStr);
                }
                currStr = "";
            } else{
                currStr += str[i];       
            }
            // cout<<i<<":"<<currStr<<endl;
        }
        if(currStr!=""){
            arr.push_back(currStr);
        }

        // for(int i=0;i<arr.size();i++){
        //     cout<<arr[i]<<" ";
        // }
        // cout<<endl;

        // prefix to postfix conversion
        list<string> stck;
        for(int i=arr.size()-1;i>=0;i--){
            if(arr[i]=="+" || arr[i]=="-" || arr[i]=="*" || arr[i]=="/"){
                string val1 = stck.back();
                stck.pop_back();
                string val2 = stck.back();
                stck.pop_back();
                stck.push_back(val1+" "+val2+" "+arr[i]); 
            } else{
                stck.push_back(arr[i]);
            }
        }
        return stck.back();
    }
```




### Remove Digits (693):

Given a non-negative integer num represented as a string, remove k digits from the number so that the new number is the smallest possible.

```cpp
    string removeKdigits(string &num, int k) {
        // write your code here.
        if(k>=num.size()){
            return "0";
        }
        list<int> stck;
        for(int i=0;i<num.size();i++){
            while(k>0 && stck.size()>0 && num[i]<num[stck.back()]){
                k--;
                stck.pop_back();
            }
            stck.push_back(i);
        }
        while(stck.size()>0 && k>0){
            stck.pop_back();
        }

        // process for result
        bool isLeadingZero = true;
        string result = "";
        for(const auto &index : stck){
            if(num[index]=='0' && isLeadingZero){
                continue;
            } else {
                isLeadingZero = false;
                result += num[index];
            }
        }
        return result.size()==0?"0":result;
    }
```



### Tall Building (285):

At the weekend, Xiao Q and his friends came to the big city for shopping. There are many tall buildings.There are n tall buildings in a row, whose height is indicated by arr.
Xiao Q has walked from the first building to the last one. Xiao Q has never seen so many buildings, so he wants to know how many buildings can he see at the location of each building? (When the height of the front building is greater than or equal to the back building, the back building will be blocked)

```cpp
     vector<int> tallBuilding(vector<int> &arr) {
        // Write your code here.
        vector<int> result(arr.size(),1);
        list<int> stck;
        for(int i=1;i<arr.size();i++){
            int val = arr[i-1];
            while(stck.size()>0 && val>=arr[stck.back()]){
                stck.pop_back();
            }
            stck.push_back(i-1);
            // cout<<"left: "<<i<<" val:"<<stck.size()<<endl;
            result[i] += stck.size();
        }

        stck.clear();
        for(int i=arr.size()-2;i>=0;i--){
            int val = arr[i+1];
            while(stck.size()>0 && val>=arr[stck.back()]){
                stck.pop_back();
            }
            stck.push_back(i+1);
            // cout<<"right: "<<i<<" val:"<<stck.size()<<endl;
            result[i] += stck.size();
        }
        return result;
    }
```


