---
layout: post
title: BFS Problem Sets Part II
published: true
---

This wiki contains a couple of well-defined problems solved via Breadth First Search (BFS) traversal.



### Pacific Atlantic Water Flow (778):

```cpp
#include <list>
#include <set>
class Solution {
public:
    /**
     * @param matrix: the given matrix
     * @return: The list of grid coordinates
     *          we will sort your return value in output
     */
    bool canVisit(pair<int,int> node, vector<vector<int>> &board, int prevVal){
        if(node.first<0 || node.first>=board.size()){
            return false;
        }
        if(node.second<0 || node.second>=board[node.first].size()){
            return false;
        }
        if(board[node.first][node.second] < prevVal){
            return false;
        }
        return true;
    }

    void bfsTraversal(vector<pair<int,int>> initialNodes, vector<vector<int>> &board, vector<vector<int>> &checkedMat){
        vector<pair<int,int>> dirArray = {{-1,0},{1,0},{0,-1},{0,1}};
        list<pair<int,int>> que;
        set<pair<int,int>> visitedNodes;
        for(int i=0;i<initialNodes.size();i++){
            que.push_back(initialNodes[i]);
            visitedNodes.insert(initialNodes[i]);
            checkedMat[initialNodes[i].first][initialNodes[i].second]++;
            // cout<<"inserting node: "<<initialNodes[i].first<<","<<initialNodes[i].second<<endl;
        }

        while(que.size()>0){
            pair<int,int> node = que.front();
            que.pop_front();

            // cout<<"("<<node.first<<","<<node.second<<")";
            
            for(pair<int,int> &dir : dirArray){
                pair<int,int> newNode = {node.first+dir.first, node.second+dir.second};
                if(canVisit(newNode, board, board[node.first][node.second]) && visitedNodes.find(newNode)==visitedNodes.end()){
                    que.push_back(newNode);
                    visitedNodes.insert(newNode);
                    checkedMat[newNode.first][newNode.second]++;
                    // cout<<"-> ("<<newNode.first<<","<<newNode.second<<")";
                }
            }
            cout<<endl;
        }
        cout<<endl;
        que.clear();
        visitedNodes.clear();
    }

    void printGraph(vector<vector<int>> &checkedMat){
        cout<<"graph start"<<endl;
        for(int i=0;i<checkedMat.size();i++){
            for(int j=0;j<checkedMat[i].size();j++){
                cout<<checkedMat[i][j]<<" ";
            }
            cout<<endl;
        }
        cout<<"graph end"<<endl;
    }
    
    vector<vector<int>> pacificAtlantic(vector<vector<int>> &matrix) {
        // write your code here
        vector<vector<int>> checkedMat(matrix.size());
        for(int i=0;i<matrix.size();i++){
            checkedMat[i].resize(matrix[i].size(), 0);
        }
        vector<pair<int,int>> initialNodes;
        for(int i=0;i<matrix.size();i++){
            initialNodes.push_back({i,0});
        }
        for(int i=1;i<matrix[0].size();i++){
            initialNodes.push_back({0,i});
        }
        // cout<<"first traversal"<<endl;
        bfsTraversal(initialNodes, matrix, checkedMat);//, {{0,1},{1,0}});
        // printGraph(checkedMat);
        initialNodes.clear();
        for(int i=0;i<matrix.size();i++){
            initialNodes.push_back({i,matrix[i].size()-1});
        }
        for(int i=0;i<matrix[matrix.size()-1].size()-1;i++){
            initialNodes.push_back({matrix.size()-1,i});
        }
        // cout<<"second traversal"<<endl;
        bfsTraversal(initialNodes, matrix, checkedMat);//, {{0,-1},{-1,0}});
        // printGraph(checkedMat);

        vector<vector<int>> result;
        for(int i=0;i<checkedMat.size();i++){
            for(int j=0;j<checkedMat[i].size();j++){
                if(checkedMat[i][j]==2){
                    result.push_back({i,j});
                }
            }
        }
        return result;
    }
};
```



### Smallest Greater Multiple Made of Two Digits (3743)
- Combinatorial problem solved via BFS

```cpp
#include <list>
class Solution {
public:
    /**
     * @param k: An integer
     * @param digit1: An integer
     * @param digit2: An integer
     * @return: The smallest multiple of k consisting only of digit1 and digit2
     */
    int findInteger(int k, int digit1, int digit2) {
        // write your code here

        list<string> que;
        if(digit1 > digit2){
            int temp = digit2;
            digit2 = digit1;
            digit1 = temp;
        }
        char ch1 = (char)'0'+(char)digit1;
        char ch2 = (char)'0'+(char)digit2;
        vector<char> dirArray = {ch1, ch2};
        for(const auto &dir: dirArray){
            string str = string(1, dir);
            que.push_back(str);
        }
        long long int maxVal = 2147483647;
        bool isFirstElement = true;
        while(que.size()>0){
            string node = que.front();
            que.pop_front();
            // cout<<node<<",";

            long long int val = stoll(node);
            // cout<<"val:"<<val<<endl;
            if(val==0){
                if(isFirstElement){
                    continue;
                } else{
                    return -1;
                }
            }
            if(val > maxVal){
                return -1;
            }
            if(val%k == 0){
                return val;
            }
            isFirstElement = false;

            for(int i=0;i<dirArray.size();i++){
                string nextNode = node + string(1,dirArray[i]);
                que.push_back(nextNode);
            }
        }
        return -1;
    }
};
```



### Smallest Common Region (3669):

```cpp
#include <map>
#include <list>
class Solution {
public:
    /**
     * @param regions: The list of regions.
     * @param region1: One of regions.
     * @param region2: One of regions.
     * @return: The smallest common region.
     */
    map<string,string> createParentMapper(vector<vector<string>> &regions){
        map<string,string> parentMapper;
        for(int i=0;i<regions.size();i++){
            for(int j=1;j<regions[i].size();j++){
                parentMapper[regions[i][j]] = regions[i][0];
            }
        }
        return parentMapper;
    }

    vector<string> findPath(map<string,string> parentMapper, string region){
        list<string> lst;
        while(parentMapper.find(region) != parentMapper.end()){
            lst.push_back(region);
            region = parentMapper[region];
        }
        lst.push_back(region);
        vector<string> result;
        while(lst.size()>0){
            result.push_back(lst.back());
            lst.pop_back();
        }
        return result;
    }

    void printPath(vector<string> &vec){
        cout<<"path: ";
        for(const string &val : vec){
            cout<<val<<" ";
        }
        cout<<endl;
    }

    string findCommon(vector<string> &path1, vector<string> &path2){
        int i=0;
        while(i<path1.size() && i<path2.size() && path1[i]==path2[i]){
            i++;
        }
        if(i==0){
            return "";
        }
        return path1[i-1];
    }

    string smallestCommonRegion(vector<vector<string>> &regions, string &region1, string &region2) {
        // --- write your code here ---
        map<string,string> parentMapper = createParentMapper(regions);
        vector<string> path1 = findPath(parentMapper, region1);
        // printPath(path1);
        vector<string> path2 = findPath(parentMapper, region2);
        // printPath(path2);
        return findCommon(path1, path2);
    }
};
```



### Minimum Genetic Mutation (1244):

```cpp
#include <list>
#include <set>
class Solution {
public:
    /**
     * @param start: 
     * @param end: 
     * @param bank: 
     * @return: the minimum number of mutations needed to mutate from "start" to "end"
     */

    bool isValidString(string &pattern, vector<string> &bank){
        for(string &str : bank){
            if(str==pattern){
                return true;
            }
        }
        return false;
    }

    int minChanges(string &start, string &end, vector<string> &bank){

        list<pair<string,int>> que;
        set<string> visited;
        que.push_back({start, 0});
        visited.insert(start);
        vector<char> charArray = {'A','C','T','G'};

        while(que.size()>0){
            string current = que.front().first;
            int mutations = que.front().second;
            que.pop_front();
            // cout<<"exploring str:"<<current<<" with mut:"<<mutations<<endl;

            if(current!=start && !isValidString(current, bank)){
                continue;
            }
            if(current==end){
                return mutations;
            }

            for(int i=0;i<current.size();i++){
                // cout<<"checking i:"<<i<<" "<<current<<","<<end<<endl;
                // ignore if current one is matching
                // if(current.at(i)==end.at(i)){
                //     continue;
                // }
                for(char &ch : charArray){
                    string next = current;
                    next.at(i) = ch;//end.at(i);
                    // cout<<"checking next:"<<next<<endl;
                    if(visited.find(next) == visited.end()){
                        que.push_back({next, mutations+1});
                        visited.insert(next);
                    }
                }
            }
        }
        return -1;
    }

    int minMutation(string &start, string &end, vector<string> &bank) {
        // Write your code here
        // if(!isValidString(end, bank)){
        //     return -1;
        // }
        return minChanges(start,end,bank);
    }
};
```



### Closest Leaf in a Binary Tree (854):

```cpp
/**
 * Definition of TreeNode:
 * class TreeNode {
 * public:
 *     int val;
 *     TreeNode *left, *right;
 *     TreeNode(int val) {
 *         this->val = val;
 *         this->left = this->right = NULL;
 *     }
 * }
 */
#include <list>
#include <set>
class Solution {
public:
    /**
     * @param root: the root
     * @param k: an integer
     * @return: the value of the nearest leaf node to target k in the tree
     */
    TreeNode* findNode(TreeNode *root, int k){
        if(!root){
            return NULL;
        }
        if(root->val == k){
            return root;
        }
        TreeNode *node = findNode(root->left, k);
        if(node){
            return node;
        }
        return findNode(root->right, k);
    }

    TreeNode* findNodePath(TreeNode *root, int k, vector<TreeNode*> &result){
        if(!root){
            return NULL;
        }
        if(root->val == k){
            result.push_back(root);
            return root;
        }
        TreeNode *node = findNodePath(root->left, k, result);
        if(node){
            result.push_back(root);
            return node;
        }
        node = findNodePath(root->right, k, result);
        if(node){
            result.push_back(root);
            return node;
        }
        return NULL;
    }

    TreeNode *findClosestLeaf(TreeNode *root, vector<TreeNode*> path){
        list<pair<TreeNode*,int>> que;
        set<TreeNode*> visitedNodes;
        if(root){
            que.push_back({root,0});
            visitedNodes.insert(root);
        }
        
        while(que.size()>0){
            TreeNode* node = que.front().first;
            int currDist = que.front().second;
            que.pop_front();
            visitedNodes.insert(node);

            // cout<<"exploring node "<<node->val;
            if(!node->left && !node->right){
                return node;
            }
            if(node->left && visitedNodes.find(node->left)==visitedNodes.end()){
                que.push_back({node->left, currDist+1});
                // cout<<" -<"<<node->left->val;
                visitedNodes.insert(node->left);
            }
            if(node->right && visitedNodes.find(node->right)==visitedNodes.end()){
                que.push_back({node->right, currDist+1});
                // cout<<" ->"<<node->right->val;
                visitedNodes.insert(node->right);
            }

            // next Node on the path
            if(path.size() >= (currDist+2)){
                TreeNode* next = path[currDist+1];
                if(visitedNodes.find(next) == visitedNodes.end()){
                    que.push_back({next, currDist+1});
                    visitedNodes.insert(next);
                }
            }
            // cout<<endl;
        }
        return NULL;
    }

    int findClosestLeaf(TreeNode *root, int k) {
        // Write your code here

        vector<TreeNode*> path;
        TreeNode *node = findNodePath(root, k, path);
        // for(TreeNode *node : path){
        //     cout<<node->val<<",";
        // }
        // cout<<endl;
        // cout<<"findNode:"<<node<<endl;
        if(!node){
            if(!root){
                return -1;
            }
            node = findClosestLeaf(root,path);
            return node->val;
        }
        node = findClosestLeaf(node,path);
        if(!node){
            return -1;
        }
        return node->val;
    }
};
```



### Minesweeper (1189):

```cpp
#include  <set>
#include  <list>
class Solution {
public:
    /**
     * @param board: a board
     * @param click: the position
     * @return: the new board
     */
    bool canVisit(pair<int,int> node, vector<vector<char>> &board){
        if(node.first<0 || node.first>=board.size()){
            return false;
        }
        if(node.second<0 || node.second>=board[board.size()-1].size()){
            return false;
        }
        // if(board[node.first][node.second]=='M' || board[node.first][node.second]=='X'){
        //     return false;
        // }
        return true;
    }

    int adjacentMineCount(pair<int,int> node, vector<vector<char>> &board){
        if(!canVisit(node, board)){
            return -1;
        }
        int count = 0;
        for(const pair<int,int> &pr : dirArray){
            pair<int,int> nextNode = {node.first+pr.first, node.second+pr.second};
            if(canVisit(nextNode,board)){
                if(board[nextNode.first][nextNode.second]=='X' || board[nextNode.first][nextNode.second]=='M'){
                    count++;
                }
            }
        }
        return count;
    }

    void printBoard(vector<vector<char>> &board){
        cout<<"board start"<<endl;
        for(int i=0;i<board.size();i++){
            for(int j=0;j<board[i].size();j++){
                cout<<board[i][j]<<" ";
            }
            cout<<endl;
        }
        cout<<"board end"<<endl;
    }

    vector<vector<char>> updateBoard(vector<vector<char>> &board, vector<int> &click) {
        // Write your code here
        
        // copy board
        vector<vector<char>> result(board.size());
        for(int i=0;i<board.size();i++){
            vector<char> vec(board[i].size());
            result[i] = vec;
            for(int j=0;j<board[i].size();j++){
                result[i][j] = board[i][j]; 
            }
        }
        // printBoard(result);

        list<pair<int,int>> que;
        set<pair<int,int>> visitedNodes;
        pair<int,int> start = {click[0], click[1]};
        if(canVisit(start, board)){
            if(board[start.first][start.second]=='X' || board[start.first][start.second]=='M'){
                result[start.first][start.second] = 'X';
                return result;
            }
            que.push_back(start);
            visitedNodes.insert(start);
        }

        while(que.size()>0){
            pair<int,int> node = que.front();
            que.pop_front();

            // cout<<"exploring node: ("<<node.first<<","<<node.second<<")"<<endl;
            if(board[node.first][node.second]=='X' || board[node.first][node.second]=='M'){
                // result[node.first][node.second] = 'X';
                continue;
            }
            if(board[node.first][node.second]=='B'){
                continue;
            }

            int count = adjacentMineCount(node, board);
            // cout<<"count:"<<count<<endl;
            if(count>0){
                // cout<<"setting value to: "<<count<<endl;
                char ch = '0'+(char)count;
                result[node.first][node.second] = ch;
                continue;
            }

            for(const pair<int,int> &pr : dirArray){
                pair<int,int> nextNode = {node.first+pr.first, node.second+pr.second};
                // cout<<" checking node ("<<nextNode.first<<","<<nextNode.second<<")"<<endl;
                if(canVisit(nextNode,board) && visitedNodes.find(nextNode)==visitedNodes.end()){
                    que.push_back(nextNode);
                    // cout<<" inserting node ("<<nextNode.first<<","<<nextNode.second<<")"<<endl;
                    visitedNodes.insert(nextNode);
                }
            }
            // cout<<"setting val to B"<<endl;
            result[node.first][node.second] = 'B';
        }

        return result;
    }

private:
    vector<pair<int,int>> dirArray = {{-1,-1},{-1,0},{-1,1}, {0,-1},{0,1}, {1,-1},{1,0},{1,1}};
};
```



### Minimum Height Trees (1298):

```cpp
#include <list>
#include <set>
#include <vector>
class Solution {
public:
    /**
     * @param n: n nodes labeled from 0 to n - 1
     * @param edges: a undirected graph
     * @return:  a list of all the MHTs root labels
     *          we will sort your return value in output
     */
    map<int, vector<int>> createGraph(int n, vector<vector<int>> &edges){
        map<int, vector<int>> graph;
        for(int i=0;i<=n;i++){
            graph[i] = {};
        }
        for(const vector<int> &vec: edges){
            int start=vec[0], end=vec[1];
            graph[start].push_back(end);
            graph[end].push_back(start);
        }
        return graph;
    }

    void printGraph(map<int, vector<int>> &graph){
        cout<<"graph start"<<endl;
        for(const auto &pr : graph){
            cout<<pr.first<<": ";
            for(const int &val : pr.second){
                cout<<val<<",";
            }
            cout<<endl;
        }
        cout<<"graph end"<<endl;
    }

    int heightBfs(int start, map<int, vector<int>> &graph){
        list<pair<int,int>> que;
        set<int> visitedNodes;
        que.push_back({start, 1});
        visitedNodes.insert(start);

        int maxHeight = 0;
        while(que.size()>0){
            int node = que.front().first;
            int currDist = que.front().second;
            que.pop_front();

            // cout<<"exploring node: "<<node<<" with dist:"<<currDist<<endl;
            maxHeight = max(maxHeight, currDist);

            for(const int &nextNode : graph[node]){
                if(visitedNodes.find(nextNode) == visitedNodes.end()){
                    // cout<<" inserting node: "<<nextNode<<endl;
                    que.push_back({nextNode, currDist+1});
                    visitedNodes.insert(nextNode);
                }
            }
        }
        return maxHeight;
    }

    vector<int> findMinHeightTrees(int n, vector<vector<int>> &edges) {
        // Write your code here
        map<int, vector<int>> graph = createGraph(n, edges);
        // printGraph(graph);

        int minHeight = n+2;
        vector<int> result;
        for(int i=0;i<n;i++){
            int height = heightBfs(i, graph);
            if(height == minHeight){
                result.push_back(i);
            } else if(height < minHeight){
                minHeight = height;
                result.clear();
                result.push_back(i);
            }
        }
        return result;

    }
};
```



### Shortest Path in a Grid with Obstacles Elimination (1723):

```cpp
#include <list>
#include <set>
class Solution {
public:
    /**
     * @param grid: a list of list
     * @param k: an integer
     * @return: Return the minimum number of steps to walk
     */
    bool canVisit(pair<int,int> node, vector<vector<int>> &board){
        if(node.first<0 || node.first>=board.size()){
            return false;
        }
        if(node.second<0 || node.second>=board[node.first].size()){
            return false;
        }
        return true;
    }

    int shortestPath(vector<vector<int>> &grid, int k) {
        // write your code here

        list< pair< pair<int,int>,pair<int,int> > > que;
        set<pair<pair<int,int>,int>> visitedNodes;
        pair<int,int> start={0,0}, end={grid.size()-1, grid[grid.size()-1].size()-1};
        que.push_back({start, {grid[0][0], 0}});
        visitedNodes.insert({start, grid[0][0]});
        vector<pair<int,int>> dirArray = {{-1,0},{1,0},{0,-1},{0,1}};

        while(que.size()>0){
            pair<int,int> node = que.front().first;
            int currObstaclesRemoved = que.front().second.first;
            int currDist = que.front().second.second;
            que.pop_front();

            if(node==end && currObstaclesRemoved<=k){
                return currDist;
            }
            if(currObstaclesRemoved > k){
                continue;
            }

            for(const pair<int,int> &dir: dirArray){
                pair<int,int> nextNode = {node.first+dir.first, node.second+dir.second};
                if(canVisit(nextNode, grid)){
                    int obstaclesRemoved = currObstaclesRemoved+grid[nextNode.first][nextNode.second];
                    if(visitedNodes.find({nextNode,obstaclesRemoved})==visitedNodes.end()){
                        que.push_back({nextNode, {obstaclesRemoved, currDist+1}});
                        visitedNodes.insert({nextNode, obstaclesRemoved});
                    }
                }
            }
        }
        return -1;
    }
};
```



### Shortest Bridge (1708):

```cpp
#include <list>
#include <set>
class Solution {
public:
    /**
     * @param a: 
     * @return: nothing
     */
    
    void printBoard(vector<vector<int>> &board){
        cout<<"graph start"<<endl;
        for(int i=0;i<board.size();i++){
            for(int j=0;j<board[i].size();j++){
                cout<<board[i][j]<<",";
            }
            cout<<endl;
        }
        cout<<"graph end"<<endl;
    }

    bool isValidBlock(pair<int,int> node, vector<vector<int>> &board){
        if(node.first<0 || node.first>=board.size()){
            return false;
        }
        if(node.second<0 || node.second>=board[node.first].size()){
            return false;
        }
        return true;
    }

    void bfsReplaceConnectedNodes(pair<int,int> startNode, vector<vector<int>> &board, int &replacedValue){
        replacedValue++;
        list<pair<int,int>> que;
        set<pair<int,int>> visitedNodes;
        int startVal = board[startNode.first][startNode.second];
        que.push_back(startNode);
        visitedNodes.insert(startNode);

        while(que.size()>0){
            pair<int,int> node = que.front();
            que.pop_front();
            board[node.first][node.second] = replacedValue;

            for(const pair<int,int> &dir : dirArray){
                pair<int,int> nextNode = {node.first+dir.first, node.second+dir.second};
                if(isValidBlock(nextNode, board) && board[nextNode.first][nextNode.second]==startVal){
                    if(visitedNodes.find(nextNode) == visitedNodes.end()){
                        que.push_back(nextNode);
                        visitedNodes.insert(nextNode);
                    }
                }
            }
        }
    }

    vector<pair<int,int>> findNodes(int val, vector<vector<int>> &board){
        vector<pair<int,int>> result;
        for(int i=0;i<board.size();i++){
            for(int j=0;j<board[i].size();j++){
                if(board[i][j]==val){
                    result.push_back({i,j});
                }
            }
        }
        return result;
    }

    int minDistanceToNode(vector<pair<int,int>> initialNodes, int target, vector<vector<int>> &board){
        list<pair< pair<int,int>,int>> que;
        set<pair<int,int>> visitedNodes;
        for(const pair<int,int> &pr: initialNodes){
            que.push_back({pr, 0});
            visitedNodes.insert(pr);
        }

        while(que.size()>0){
            pair<int,int> node = que.front().first;
            int currDist = que.front().second;
            que.pop_front();
            // cout<<"exploring node: ("<<node.first<<","<<node.second<<")"<<endl;

            if(board[node.first][node.second]==target){
                return currDist-1;
            }
            for(const pair<int,int> &dir : dirArray){
                pair<int,int> nextNode = {node.first+dir.first, node.second+dir.second};
                // cout<<" checking node: ("<<nextNode.first<<","<<nextNode.second<<")"<<endl;
                if(isValidBlock(nextNode, board) && visitedNodes.find(nextNode)==visitedNodes.end()){
                    // cout<<" inserting node: ("<<nextNode.first<<","<<nextNode.second<<")"<<endl;
                    que.push_back({nextNode, currDist+1});
                    visitedNodes.insert(nextNode);
                }
            }
        }
        return -1;
    }

    int shortestBridge(vector<vector<int>> &a) {
        //
        int replacedValue=10; 
        for(int i=0;i<a.size();i++){
            for(int j=0;j<a[i].size();j++){
                if(a[i][j]==1){
                    bfsReplaceConnectedNodes({i,j},a,replacedValue);
                }
            }
        }
        // printBoard(a);
        vector<pair<int,int>> initialNodes = findNodes(11, a);
        return minDistanceToNode(initialNodes, 12, a);
    }

private:
    vector<pair<int,int>> dirArray = {{1,0},{-1,0},{0,1},{0,-1}};
};
```



### Absolutely Continuous Numbers (3650):

```cpp
#include <list>
#include <set>

class Solution {
public:
    /**
     * @param mi: Minimum value of the range.
     * @param ma: Maximum value of the range.
     * @return: All the completely continuous numbers in the range.
     */
    vector<int> listCompletelyContinuousNumbers(int mi, int ma) {
        // --- write your code here ---

        list<string> que;
        set<string> visitedNodes;
        for(int i=0;i<10;i++){
            string str = string(1, '0'+(char)i);
            que.push_back(str);
            visitedNodes.insert(str);
        }

        while(que.size()>0){
            string current = que.front();
            que.pop_front();
            // cout<<"exploring string:"<<current<<endl;

            int val = stoll(current);
            if(val > ma){
                continue;
            }

            for(int i=0;i<10;i++){
                char ch = current[current.size()-1];
                if(ch > '0'){
                    string str1 = current + string(1,ch-1);
                    if(visitedNodes.find(str1) == visitedNodes.end()){
                        // cout<<"inserting string1:"<<str1<<endl;
                        que.push_back(str1);
                        visitedNodes.insert(str1);
                    }
                }
                if(ch < '9'){
                    string str2 = current + string(1,ch+1);
                    if(visitedNodes.find(str2) == visitedNodes.end()){
                        // cout<<"inserting string2:"<<str2<<endl;
                        que.push_back(str2);
                        visitedNodes.insert(str2);
                    }
                }
            }
        }

        set<int> visitedNums;
        for(const string &str : visitedNodes){
            int val = stoi(str);
            visitedNums.insert(val);
        }

        vector<int> result;
        for(const int &val : visitedNums){
            if(val>=mi && val<=ma){
                result.push_back(val);
            }
        }
        return result;
    }
};
```



### Shortest Path in the Maze (3727):

```cpp
/**
 * Definition of MazeMaster:
 * class MazeMaster {
 * public:
 *      bool canMove(char direction);
 *      void move(char direction);
 *      bool isEndpoint();
 * };
 * You should not implement it, or speculate about its implementation.
 */

#include <list>
#include <set>

class Solution {
public:
    /**
     * @param master: The object to access the maze.
     * @return: The length of shortest path in the maze.
     */
    
    void dfs(MazeMaster &master, list<char> &moves, int &minLen, pair<int,int> currPosition, set<pair<int,int>> &visitedNodes){
        // cout<<"current move size:"<<moves.size()<<" with position:("<<currPosition.first<<","<<currPosition.second<<")"<<endl;
        if(visitedNodes.find(currPosition) != visitedNodes.end()){
            return;
        }
        if(master.isEndpoint()){
            if(minLen < 1){
                minLen = (int)moves.size();
            } else {
                minLen = min(minLen, (int)moves.size());
            }
            return;
        }
        if(minLen>0 && moves.size()>=minLen){
            return;
        }
        visitedNodes.insert(currPosition);
        for(int i=0;i<directions.size();i++){
            char dir = directions[i];
            char revDir = reverseDirections[i];
            if(!master.canMove(dir)){
                continue;
            }
            pair<int,int> nextPosition = {currPosition.first+dirArray[i].first, currPosition.second+dirArray[i].second};
            master.move(dir);
            moves.push_back(dir);
            dfs(master, moves, minLen, nextPosition, visitedNodes);
            moves.pop_back();
            master.move(revDir);
        }
        visitedNodes.erase(currPosition);// q: how to remove???
    }

    int findShortestPath(MazeMaster &master) {
        // --- write your code here ---
        list<char> moves;
        int minLen = -1;
        pair<int,int> currPosition = {0,0};
        set<pair<int,int>> visitedNodes;
        dfs(master, moves, minLen, currPosition, visitedNodes);
        return minLen;
    }

private:
    vector<char> directions = {'U','D','L','R'};
    vector<char> reverseDirections = {'D','U','R','L'};
    vector<pair<int,int>> dirArray = {{-1,0},{1,0},{0,-1},{0,1}};
};
```



### Shortest Path in Matrix (1888):

```cpp
#include <list>
#include <set>
class Solution {
public:
    /**
     * @param grid: the input matrix
     * @return: the new matrix
     */
    bool canVisit(pair<int,int> node, vector<vector<int>> &board){
        if(node.first<0 || node.first>=board.size()){
            return false;                                        
        }
        if(node.second<0 || node.second>=board[node.first].size()){
            return false;
        }
        if(board[node.first][node.second]==-1){
            return false;
        }
        if(board[node.first][node.second]!=0 && board[node.first][node.second]!=1){
            return false;
        }
        return true;
    }

    vector<pair<int,int>> findStartPoints(vector<vector<int>> &board){
        vector<pair<int,int>> result;
        for(int i=0;i<board.size();i++){
            for(int j=0;j<board[i].size();j++){
                if(board[i][j]==1){
                    result.push_back({i,j});
                }
            }
        }
        return result;
    }

    void bfsFindShortest(vector<vector<int>> &board){
        list<pair<pair<int,int>, int>> que;
        set<pair<int,int>> visitedNodes;
        vector<pair<int,int>> dirArray = {{1,0},{-1,0},{0,1},{0,-1}};
        vector<int> dirCharArray = {2,3,4,5};
        vector<pair<int,int>> initialPoints = findStartPoints(board);
        for(int i=0;i<initialPoints.size();i++){
            // cout<<"inserting initial point:("<<initialPoints[i].first<<","<<initialPoints[i].second<<")"<<endl;
            que.push_back({ initialPoints[i], 2 });
            // visitedNodes.insert(initialPoints[i]);
        }

        while(que.size()>0){
            pair<int,int> node = que.front().first;
            int dir = que.front().second;
            que.pop_front();

            // cout<<"exploring node: ("<<node.first<<","<<node.second<<")"<<endl;
            if(board[node.first][node.second] == 0){
                board[node.first][node.second]=dir;
            } else if(board[node.first][node.second] != -1){
                board[node.first][node.second] = min(board[node.first][node.second], dir);
            }
            visitedNodes.insert(node);

            for(int i=0;i<dirArray.size();i++){
                pair<int,int> dir = dirArray[i];
                pair<int,int> nextNode = {node.first+dir.first, node.second+dir.second};
                // cout<<"checking node: ("<<nextNode.first<<","<<nextNode.second<<")"<<endl;
                if(canVisit(nextNode,board) && visitedNodes.find(nextNode)==visitedNodes.end()){
                    // cout<<"inserting node: ("<<nextNode.first<<","<<nextNode.second<<") with dir:"<<dirCharArray[i]<<endl;
                    que.push_back({nextNode, dirCharArray[i]});
                    // visitedNodes.insert(nextNode);
                }
            }
        }
    }

    vector<vector<int>> shortestPath(vector<vector<int>> &grid) {
        // write your code here
        bfsFindShortest(grid);
        return grid;
    }
};
```
