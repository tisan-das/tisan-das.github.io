---
layout: post
title: BFS Problem Sets Part I
published: true
---

This wiki contains a couple of well-defined problems solved via Breadth First Search (BFS) traversal.


The following points to be noted while solving traversal problems, especially using BFS with C++:
- Node is marked as visited only when it's explored fully. This would be useful for especially Dijkstra's shortest-path algorithm
- Skip the use of set for visited nodes if possible, rather use the original matrix
- Use unordered_map and unordered_set instead of map and set. Please note unordered data structures contain hash for only primitive data types, and not for complex data types like pair. Unordered data structures are useful to overcome TLE-related issues 

Topological sort is useful on Directed Acyclic Graphs. The relationship A->B signifies that B is dependent on A. Topological sort can't be used on undirected graphs, all the edges would inherently create a cycle in an undirected graph.

Problems related to bipartite graphs can also be solved with BFS, with an added layer of 2 color problems. If a node is visited, all the associated nodes would be colored with opposite colors, and if that's not possible, then it's not a bipartite graph.


If using online compilers, the following boilerplate code can be used:

```cpp
#include <iostream>
using namespace std;

int main() {
    // Write C++ code here
    TreeNode *treeNode = new TreeNode(10);
    treeNode->right = new TreeNode(20);
    
    Solution solution;
    string str = solution.serialize(treeNode);
    cout<<"serialized string: "<<str<<endl;
    
    return 0;
}
```

### Clone Graph (137):

```cpp
/**
 * Definition for undirected graph.
 * struct UndirectedGraphNode {
 *     int label;
 *     vector<UndirectedGraphNode *> neighbors;
 *     UndirectedGraphNode(int x) : label(x) {};
 * };
 */

#include <map>

class Solution {
public:
    /**
     * @param node: A undirected graph node
     * @return: A undirected graph node
     */
    UndirectedGraphNode* cloneGraph(UndirectedGraphNode *node) {
        // write your code here
        if(!node){
            return NULL;
        }
        // cout<<"checking node val:"<<node->label<<endl;
        UndirectedGraphNode* clonedNode = NULL;
        if(clonedNodeMapper.find(node) != clonedNodeMapper.end()){
            clonedNode = clonedNodeMapper[node];
            return clonedNode;
        } else {
            clonedNode = new UndirectedGraphNode(node->label);
            clonedNodeMapper[node] = clonedNode;
        }

        for(int i=0;i<node->neighbors.size();i++){
            clonedNode->neighbors.push_back(cloneGraph(node->neighbors[i]));
        }
        return clonedNode;
    }

private:
    map<UndirectedGraphNode*,UndirectedGraphNode*> clonedNodeMapper;
};
```



### Number of Big Islands (677):

```cpp
#include <list>
class Solution {
public:
    /**
     * @param grid: a 2d boolean array
     * @param k: an integer
     * @return: the number of Islands
     */
    
    pair<int,int> isIslandPresent(vector<vector<bool>> &grid){
        
        return make_pair(-1,-1);
    }

    bool isValid(pair<int,int> node, vector<vector<bool>> &grid){
        if(node.first<0 || node.first>=grid.size()){
            return false;
        }
        if(node.second<0 || node.second>=grid[node.first].size()){
            return false;
        }
        if(!grid[node.first][node.second]){
            return false;
        }
        return true;
    }

    int numsofIsland(vector<vector<bool>> &grid, int k) {
        // Write your code here

        int count = 0;

        for(int i=0;i<grid.size();i++){
            for(int j=0;j<grid[i].size();j++){
                if(!grid[i][j]){
                    continue;
                }


                pair<int,int> rootNode = make_pair(i,j);//isIslandPresent(grid);
                list<pair<int,int>> que;
                // set<pair<int,int>> visitedNodes;
                if(rootNode.first==-1 && rootNode.second==-1){
                    break;
                }
                que.push_back(rootNode);
                grid[rootNode.first][rootNode.second] = false;
                int currSize = 0;

                while(que.size()>0){
                    pair<int,int> node = que.front();
                    // cout<<"node:"<<node.first<<","<<node.second<<endl;
                    que.pop_front();
                    currSize++;
                    // if(visitedNodes.find(node) != visitedNodes.end()){
                    //     continue;
                    // }
                    // visitedNodes.insert(node);
                    if(isValid(make_pair(node.first-1,node.second), grid)){
                        que.push_back(make_pair(node.first-1,node.second));
                        grid[node.first-1][node.second] = false;
                    }
                    if(isValid(make_pair(node.first+1,node.second), grid)){
                        que.push_back(make_pair(node.first+1,node.second));
                        grid[node.first+1][node.second] = false;
                    }
                    if(isValid(make_pair(node.first,node.second-1), grid)){
                        que.push_back(make_pair(node.first,node.second-1));
                        grid[node.first][node.second-1] = false;
                    }
                    if(isValid(make_pair(node.first,node.second+1), grid)){
                        que.push_back(make_pair(node.first,node.second+1));
                        grid[node.first][node.second+1] = false;
                    }
                }
                if(currSize >= k){
                    count++;
                }
            }
        }

        return count;
    }
};
```



### Walls and Gates (663):
- Use of BFS to find out shortest path

```cpp
#include <list>
class Solution {
public:
    /**
     * @param rooms: m x n 2D grid
     * @return: nothing
     */
    

    bool isVisitNeeded(pair<int,int> node,vector<vector<int>> &rooms){
        if(node.first<0 || node.first>=rooms.size()){
            return false;
        }
        if(node.second<0 || node.second>=rooms[node.first].size()){
            return false;
        }
        if(rooms[node.first][node.second] != infVal){
            return false;
        }
        return true;
    }

    void bfsTraverse(vector<vector<int>> &rooms){
        list<pair< pair<int,int>,int>> que;
        for(int i=0;i<rooms.size();i++){
            for(int j=0;j<rooms[i].size();j++){
                if(rooms[i][j]==0){
                    que.push_back(make_pair( make_pair(i,j) ,0));           
                }
            }
        }

        while(que.size()>0){
            pair<int,int> node = que.front().first;
            int currDistance = que.front().second;
            que.pop_front();

            if(isVisitNeeded(make_pair(node.first-1, node.second), rooms)){
                que.push_back(make_pair(make_pair(node.first-1, node.second),currDistance+1));
                rooms[node.first-1][node.second] = currDistance+1;
            }
            if(isVisitNeeded(make_pair(node.first+1, node.second), rooms)){
                que.push_back(make_pair(make_pair(node.first+1, node.second),currDistance+1));
                rooms[node.first+1][node.second] = currDistance+1;
            }
            if(isVisitNeeded(make_pair(node.first, node.second-1), rooms)){
                que.push_back(make_pair(make_pair(node.first, node.second-1),currDistance+1));
                rooms[node.first][node.second-1] = currDistance+1;
            }
            if(isVisitNeeded(make_pair(node.first, node.second+1), rooms)){
                que.push_back(make_pair(make_pair(node.first, node.second+1),currDistance+1));
                rooms[node.first][node.second+1] = currDistance+1;
            }
        }
    }

    void wallsAndGates(vector<vector<int>> &rooms) {
        // write your code here

        bfsTraverse(rooms);
    }

private:
    int infVal = 2147483647;
};
```



### Surrounded Regions (477):

```cpp
#include <list>
class Solution {
public:
    /*
     * @param board: board a 2D board containing 'X' and 'O'
     * @return: nothing
     */
    bool isVisitNeeded(pair<int,int> node, vector<vector<char>> &board){
        if(node.first<0 || node.first>=board.size()){
            return false;
        }
        if(node.second<0 || node.second>=board[node.first].size()){
            return false;
        }
        if(board[node.first][node.second] != 'O'){
            return false;
        }
        return true;
    }

    void bfsTraverse(vector<vector<char>> &board){
        list<pair<int,int>> que;
        for(int i=0;i<board.size();i++){
            if(isVisitNeeded(make_pair(i,0),board)){
                que.push_back(make_pair(i,0));
                board[i][0] = 'V';
            }
            if(board[i].size()>1 && isVisitNeeded(make_pair(i,board[i].size()-1),board)){
                que.push_back(make_pair(i,board[i].size()-1));
                board[i][board[i].size()-1] = 'V';
            }
        }
        if(board.size()>0){
            for(int j=0;j<board[0].size();j++){
                if(isVisitNeeded(make_pair(0,j),board)){
                    que.push_back(make_pair(0,j));
                    board[0][j] = 'V';
                }
            }
        }
        if(board.size()>1){
            for(int j=0;j<board[board.size()-1].size();j++){
                if(isVisitNeeded(make_pair(board.size()-1,j),board)){
                    que.push_back(make_pair(board.size()-1,j));
                    board[board.size()-1][j] = 'V';
                }
            }
        }

        while(que.size()>0){
            pair<int,int> node = que.front();
            que.pop_front();
            if(isVisitNeeded(make_pair(node.first-1,node.second),board)){
                que.push_back(make_pair(node.first-1,node.second));
                board[node.first-1][node.second] = 'V';
            }
            if(isVisitNeeded(make_pair(node.first+1,node.second),board)){
                que.push_back(make_pair(node.first+1,node.second));
                board[node.first+1][node.second] = 'V';
            }
            if(isVisitNeeded(make_pair(node.first,node.second-1),board)){
                que.push_back(make_pair(node.first,node.second-1));
                board[node.first][node.second-1] = 'V';
            }
            if(isVisitNeeded(make_pair(node.first,node.second+1),board)){
                que.push_back(make_pair(node.first,node.second+1));
                board[node.first][node.second+1] = 'V';
            }
        }

        for(int i=0;i<board.size();i++){
            for(int j=0;j<board[i].size();j++){
                if(board[i][j]=='O'){
                    board[i][j] = 'X';
                }
            }
        }
        for(int i=0;i<board.size();i++){
            for(int j=0;j<board[i].size();j++){
                if(board[i][j]=='V'){
                    board[i][j] = 'O';
                }
            }
        }
    }

    void surroundedRegions(vector<vector<char>> &board) {
        // write your code here
        bfsTraverse(board);
    }
};
```


### Course Schedule (615):
- Topological Sort

```cpp
#include <list>
#include <map>
class Solution {
public:
    /**
     * @param numCourses: a total of n courses
     * @param prerequisites: a list of prerequisite pairs
     * @return: true if can finish all courses or false
     */
    

    bool canFinish(int numCourses, vector<vector<int>> &prerequisites) {
        // write your code here

        // cycle detection though union-find
        // there can be duplicate edges
        // directed graph, hence disjoint set union algo can't be used
        // use topological sort => it can't be used with undirected graph, due to cycle detection
        
        map<int,int> inDegrees;
        map<int,vector<int>> edges;
        for(int i=0;i<prerequisites.size();i++){
            edges[prerequisites[i][0]].push_back(prerequisites[i][1]);
            inDegrees[prerequisites[i][1]]++;
        }

        list<int> que, result;
        for(int i=0;i<numCourses;i++){
            if(inDegrees[i]==0){
                que.push_back(i);
            }
        }
        while(que.size()>0){
            int node = que.front();
            que.pop_front();
            // cout<<"checking node:"<<node<<endl;
            result.push_back(node);
            for(int i=0;i<edges[node].size();i++){
                int targetNode = edges[node][i];
                inDegrees[targetNode]--;
                if(inDegrees[targetNode]==0){
                    que.push_back(targetNode);
                }
            }
        }
        return result.size()==numCourses;
    }

};
```



### Course Schedule II (616):

```cpp
#include <list>
class Solution {
public:
    /**
     * @param numCourses: a total of n courses
     * @param prerequisites: a list of prerequisite pairs
     * @return: the course order
     */
    vector<int> findOrder(int numCourses, vector<vector<int>> &prerequisites) {
        // write your code here

        map<int,int> inDegMapper;
        map<int,vector<int>> edgeMapper;
        for(int i=0;i<prerequisites.size();i++){
            edgeMapper[prerequisites[i][1]].push_back(prerequisites[i][0]);
            inDegMapper[prerequisites[i][0]]++;
        }

        list<int> que;
        vector<int> result;
        for(int i=0;i<numCourses;i++){
            if(inDegMapper[i]==0){
                que.push_back(i);
            }
        }
        while(que.size()>0){
            int node = que.front();
            que.pop_front();
            result.push_back(node);

            for(int i=0;i<edgeMapper[node].size();i++){
                int targetNode = edgeMapper[node][i];
                inDegMapper[targetNode]--;
                if(inDegMapper[targetNode]==0){
                    que.push_back(targetNode);
                }
            }
        }

        if(result.size()!=numCourses){
            result.clear();
        }
        return result;
    }
};
```



### Is Graph Bipartite? (1031):

```
#include <map>
class Solution {
public:
    /**
     * @param graph: the given undirected graph
     * @return:  return true if and only if it is bipartite
     */
    bool isBipartite(vector<vector<int>> &graph) {
        // Write your code here

        // undirect graph + grap coloring problem: 2 color
        map<int,int> nodeColorMapper; // color is 1,2
        for(int i=0;i<graph.size();i++){
            for(int j=0;j<graph[i].size();j++){
                int start=i,end=graph[i][j];
                int startColor = -1, endColor=-1;
                if(nodeColorMapper.find(start) != nodeColorMapper.end()){
                    startColor = nodeColorMapper[start];
                }
                if(nodeColorMapper.find(end) != nodeColorMapper.end()){
                    endColor = nodeColorMapper[end];
                }

                // if(startColor==-1 && endColor==-1){
                //     // randomly assign color
                //     nodeColorMapper[start] = 1;
                //     nodeColorMapper[end] = 2;
                // } else 
                if(startColor!=-1 && startColor==endColor){
                    return false;
                } else{
                    if(startColor==-1){
                        startColor = endColor==1?2:1;
                    }
                    if(endColor==-1){
                        endColor = startColor==1?2:1;
                    }
                    nodeColorMapper[start] = startColor;
                    nodeColorMapper[end] = endColor;
                }
                // cout<<"start:"<<start<<" end:"<<end<<" startColor:"<<startColor<<" endColor:"<<endColor<<endl;
            }
        }
        return true;
    }
};
```



### Strobogrammatic Number II (776):
- Corner case

```cpp
class Solution {
public:
    /**
     * @param n: the length of strobogrammatic number
     * @return: All strobogrammatic numbers
     *          we will sort your return value in output
     */
    
    void findStrobogrammatic(int remDigits, string prefix, string suffix, vector<string> &result){
        if(remDigits<=0){
            string str = prefix+suffix;
            result.push_back(str);
        }else if(remDigits<0){
            return;
        } else {
            for(auto &pr : rotateNumMapper){
                if(prefix.size()==0 && pr.first==0 && remDigits!=1){
                    continue;
                }
                if(remDigits==1){
                    if(pr.first==6 || pr.first==9){
                        continue;
                    }
                }
                string updatedPrefix = prefix + (char)('0'+pr.first);
                string updatedSuffix = suffix;
                // cout<<"pair:"<<pr.first<<","<<pr.second<<endl;
                if(remDigits!=1){
                    updatedSuffix = (char)('0'+pr.second);
                    updatedSuffix += suffix;
                }
                // cout<<"remDigits:"<<remDigits<<" prefix:"<<updatedPrefix<<" suffix:"<<updatedSuffix<<endl;
                findStrobogrammatic(remDigits-2, updatedPrefix, updatedSuffix, result);
            }
        }
    }

    vector<string> findStrobogrammatic(int n) {
        // write your code here
        rotateNumMapper[0] = 0;
        rotateNumMapper[1] = 1;
        rotateNumMapper[6] = 9;
        rotateNumMapper[8] = 8;
        rotateNumMapper[9] = 6;

        vector<string> result;
        findStrobogrammatic(n, "", "", result);
        return result;
    }

private:
    map<int,int> rotateNumMapper;
};
```



### Knight Shortest Path (611):

```cpp
#include <list>
#include <map>
/**
 * Definition for a point.
 * struct Point {
 *     int x;
 *     int y;
 *     Point() : x(0), y(0) {}
 *     Point(int a, int b) : x(a), y(b) {}
 * };
 */

class Solution {
public:
    /**
     * @param grid: a chessboard included 0 (false) and 1 (true)
     * @param source: a point
     * @param destination: a point
     * @return: the shortest path 
     */
    bool canVisit(pair<int,int> node, vector<vector<bool>> &grid){
        if(node.first<0 || node.first>=grid.size()){
            return false;
        }
        if(node.second<0 || node.second>=grid[node.first].size()){
            return false;
        }
        if(grid[node.first][node.second]!=0){
            return false;
        }
        return true;
    }

    int shortestPath(vector<vector<bool>> &grid, Point source, Point destination) {
        // write your code here
        pair<int,int> sourceNode = make_pair(source.x, source.y);
        pair<int,int> targetNode = make_pair(destination.x, destination.y);

        list<pair<pair<int,int>,int>> que;
        set<pair<int,int>> visitedNodes;
        que.push_back(make_pair(sourceNode,0));
        visitedNodes.insert(sourceNode);

        while(que.size()>0){
            pair<int,int> node = que.front().first;
            int currDist = que.front().second;
            que.pop_front();

            if(node==targetNode){
                return currDist;
            }

            pair<int,int> nextNode = make_pair(node.first+1, node.second+2);
            if(canVisit(nextNode, grid) && visitedNodes.find(nextNode)==visitedNodes.end()){
                que.push_back(make_pair(nextNode, currDist+1));
                visitedNodes.insert(nextNode);
            }

            nextNode = make_pair(node.first+1, node.second-2);
            if(canVisit(nextNode, grid) && visitedNodes.find(nextNode)==visitedNodes.end()){
                que.push_back(make_pair(nextNode, currDist+1));
                visitedNodes.insert(nextNode);
            }

            nextNode = make_pair(node.first-1, node.second+2);
            if(canVisit(nextNode, grid) && visitedNodes.find(nextNode)==visitedNodes.end()){
                que.push_back(make_pair(nextNode, currDist+1));
                visitedNodes.insert(nextNode);
            }

            nextNode = make_pair(node.first-1, node.second-2);
            if(canVisit(nextNode, grid) && visitedNodes.find(nextNode)==visitedNodes.end()){
                que.push_back(make_pair(nextNode, currDist+1));
                visitedNodes.insert(nextNode);
            }

            nextNode = make_pair(node.first+2, node.second+1);
            if(canVisit(nextNode, grid) && visitedNodes.find(nextNode)==visitedNodes.end()){
                que.push_back(make_pair(nextNode, currDist+1));
                visitedNodes.insert(nextNode);
            }

            nextNode = make_pair(node.first+2, node.second-1);
            if(canVisit(nextNode, grid) && visitedNodes.find(nextNode)==visitedNodes.end()){
                que.push_back(make_pair(nextNode, currDist+1));
                visitedNodes.insert(nextNode);
            }

            nextNode = make_pair(node.first-2, node.second+1);
            if(canVisit(nextNode, grid) && visitedNodes.find(nextNode)==visitedNodes.end()){
                que.push_back(make_pair(nextNode, currDist+1));
                visitedNodes.insert(nextNode);
            }

            nextNode = make_pair(node.first-2, node.second-1);
            if(canVisit(nextNode, grid) && visitedNodes.find(nextNode)==visitedNodes.end()){
                que.push_back(make_pair(nextNode, currDist+1));
                visitedNodes.insert(nextNode);
            }
        }
        return -1;
    }
};
```



### Snakes and Ladders (1732):

```cpp
#include <list>
#include <set>
class Solution {
public:
    /**
     * @param board: board
     * @return: snakesAndLadders
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

    pair<int,int> convertNumToNode(int num, vector<vector<int>> &board){
        // num := [0..N*N-1]
        int cols = board.size();
        int rowIndex = (cols-1)-(num/cols);
        int colIndex = num%cols;
        if((num/cols)%2 == 1){
            colIndex = (cols-1)- (num%cols);
        }
        return make_pair(rowIndex,colIndex);
    }

    int snakesAndLadders(vector<vector<int>> &board) {
        // 

        list<pair<int,int>> que;
        set<int> visitedNodes;
        que.push_back(make_pair(0,0));
        visitedNodes.insert(0);

        while(que.size()>0){
            int node = que.front().first;
            int currDist = que.front().second;
            que.pop_front();

            if(node == board.size()*board.size()-1){
                return currDist;
            }
            // cout<<"exploring node:"<<node<<" with dist:"<<currDist<<endl;

            int nextNode = node;
            for(int i=1;i<=6;i++){
                nextNode = node+i;
                pair<int,int> convNode = convertNumToNode(nextNode, board);
                if(canVisit(convNode,board)){
                    if(board[convNode.first][convNode.second]!=-1){
                        nextNode = board[convNode.first][convNode.second]-1;
                    }
                    // cout<<nextNode<<"("<<convNode.first<<","<<convNode.second<<"), ";
                    // convNode = convertNumToNode(nextNode, board);
                    if(visitedNodes.find(nextNode)==visitedNodes.end()){
                        que.push_back(make_pair(nextNode,currDist+1));
                        visitedNodes.insert(nextNode);
                    }
                }     
            }
            // cout<<endl;
        }
        return -1;
    }
};
```



### Minimum Step (1832):
- Use of unordered map and unordered set to overcome TLE

```cpp
#include <unordered_map>
#include <unordered_set>
#include <list>
class Solution {
public:
    /**
     * @param colors: the colors of grids
     * @return: return the minimum step from position 0 to position n - 1
     */
    // avoid graph construction for tle issues
    // map<int, vector<int>> convertToGraph(vector<int> &colors){
    //     map<int,vector<int>> colorMapper;
    //     for(int i=0;i<colors.size();i++){
    //         colorMapper[colors[i]].push_back(i);
    //     }

    //     map<int, vector<int>> graph;
    //     for(int i=0;i<colors.size();i++){
    //         if(i<colors.size()-1){
    //             graph[i].push_back(i+1);
    //         }
    //         for(int tgt : colorMapper[colors[i]]){
    //             if(tgt != i){
    //                 graph[i].push_back(tgt);
    //             }
    //         }
    //     }
    //     return graph;
    // }

    // void printGraph(map<int, vector<int>> &graph){
    //     cout<<"graph start"<<endl;
    //     for(auto &pr : graph){
    //         cout<<pr.first<<": ";
    //         for(int &val: pr.second){
    //             cout<<val<<", ";
    //         }
    //         cout<<endl;
    //     }
    //     cout<<"graph end"<<endl;
    // }

    int minimumStep(vector<int> &colors) {
        // write your code here

        unordered_map<int,vector<int>> colorMapper;
        for(int i=0;i<colors.size();i++){
            colorMapper[colors[i]].push_back(i);
        }
        // printGraph(colorMapper);

        int source=0, target=colors.size()-1;
        list<pair<int,int>> que;
        unordered_set<int> visitedNodes;
        unordered_set<int> visitedColors;
        que.push_back(make_pair(source,0));
        visitedNodes.insert(0);
        while(que.size()>0){
            int node = que.front().first;
            int currDist = que.front().second;
            que.pop_front();

            if(node==target){
                return currDist;
            }

            // cout<<"exploring node "<<node<<": ";
            int nextNode = node+1;
            if(visitedNodes.find(nextNode) == visitedNodes.end()){
                // cout<<nextNode<<", ";
                que.push_back(make_pair(nextNode, currDist+1));
                visitedNodes.insert(nextNode);
            }

            if(node>0){
                nextNode = node-1;
                if(visitedNodes.find(nextNode) == visitedNodes.end()){
                    // cout<<nextNode<<", ";
                    que.push_back(make_pair(nextNode, currDist+1));
                    visitedNodes.insert(nextNode);
                }
            }
            if(visitedColors.find(colors[node]) != visitedColors.end()){
                // all the nodes with same color is already visited
                continue;
            }

            for(int nextNode : colorMapper[colors[node]]){
                if(visitedNodes.find(nextNode) == visitedNodes.end()){
                    // cout<<nextNode<<", ";
                    que.push_back(make_pair(nextNode, currDist+1));
                    visitedNodes.insert(nextNode);
                }
            }
            visitedColors.insert(colors[node]);
            // cout<<endl;
        }
        return -1;
    }
};
```



### Topological Sorting (127):

```cpp
/**
 * Definition for Directed graph.
 * struct DirectedGraphNode {
 *     int label;
 *     vector<DirectedGraphNode *> neighbors;
 *     DirectedGraphNode(int x) : label(x) {};
 * };
 */
#include <list>
#include <map>
class Solution {
public:
    /**
     * @param graph: A list of Directed graph node
     * @return: Any topological order for the given graph.
     */
    vector<DirectedGraphNode*> topSort(vector<DirectedGraphNode*> graph) {
        // write your code here
        vector<DirectedGraphNode*> result;

        map<DirectedGraphNode*,int> inDegMapper;
        map<DirectedGraphNode*,int> nodePositionMapper;
        for(int i=0;i<graph.size();i++){
            inDegMapper[graph[i]] = inDegMapper[graph[i]]; 
            for(int j=0;j<graph[i]->neighbors.size();j++){
                inDegMapper[graph[i]->neighbors[j]]++;
                nodePositionMapper[graph[i]] = i;
            }
        }

        list<DirectedGraphNode*> que;
        for(auto &pr : inDegMapper){
            if(pr.second==0){
                que.push_back(pr.first);
            }
        }
        while(que.size()>0){
            DirectedGraphNode* node = que.front();
            que.pop_front();
            result.push_back(node);

            for(DirectedGraphNode* nextNode : graph[nodePositionMapper[node]]->neighbors){
                inDegMapper[nextNode]--;
                if(inDegMapper[nextNode]==0){
                    que.push_back(nextNode);
                }
            }
        }
        return result;
    }
};
```



### Sequence Reconstruction (605):

```cpp
#include <list>
#include <map>
class Solution {
public:
    /**
     * @param org: a permutation of the integers from 1 to n
     * @param seqs: a list of sequences
     * @return: true if it can be reconstructed only one or false
     */
    bool sequenceReconstruction(vector<int> &org, vector<vector<int>> &seqs) {
        // write your code here
        // topological sort => at each level there should be only one node explored

        vector<int> result;
        map<int,int> inDegMapper;
        for(int i=0;i<org.size();i++){
            inDegMapper[org[i]] = 0;
        }

        bool isEntryExists = false;
        map<int,vector<int>> graph;
        for(int i=0;i<seqs.size();i++){
            for(int j=1;j<seqs[i].size();j++){
                graph[seqs[i][j-1]].push_back(seqs[i][j]); 
                inDegMapper[seqs[i][j]]++;
                isEntryExists = true;
            }
        }

        list<int> que;
        for(auto &pr : inDegMapper){
            if(pr.second==0){
                que.push_back(pr.first);
                // cout<<pr.first<<",";
            }
        }
        // cout<<endl;
        while(que.size()>0){
            // cout<<"que size: "<<que.size()<<endl;
            if(que.size()>1){
                return false;
            }
            int node = que.front();
            que.pop_front();
            // cout<<"exploring "<<node<<": ";

            // insert into array and check any inconsistency
            result.push_back(node);
            if(org.size()<result.size() || org[result.size()-1]!=node){
                return false;
            }

            list<int> nextQue;
            for(int nextNode : graph[node]){
                inDegMapper[nextNode]--;
                if(inDegMapper[nextNode]==0){
                    nextQue.push_back(nextNode);
                    // cout<<nextNode<<", ";
                }
            }
            que = nextQue;
            // cout<<endl;
        }
        return true;

    }
};
```



### Parallel Courses (3673):

```cpp
#include <list>
class Solution {
public:
    /**
     * @param n: the number of courses
     * @param relations: the relationship between all courses
     * @return: ehe minimum number of semesters required to complete all courses
     */
    map<int, vector<int>> convertGraph(int n, vector<vector<int>> &relations){
        map<int, vector<int>> graph;
        for(int i=1;i<=n;i++){
            graph[i] = {};
        }
        for(int i=0;i<relations.size();i++){
            graph[relations[i][0]].push_back(relations[i][1]); 
        }
        return graph;
    }

    int minimumSemesters(int n, vector<vector<int>> &relations) {
        // write your code here
        map<int, vector<int>> graph = convertGraph(n, relations);

        map<int,int> inDegMapper;
        for(int i=1;i<=n;i++){
            inDegMapper[i] = 0;
        }
        for(int i=0;i<relations.size();i++){
            inDegMapper[relations[i][1]]++;
        }

        list<int> que;
        // set<int> visitedNodes;
        for(int i=1;i<=n;i++){
            if(inDegMapper[i]==0){
                que.push_back(i);
                // visitedNodes.insert(i);
            }
        }
        int semesters = 0;
        vector<int> result;
        while(que.size()>0){
            semesters++;
            list<int> nextQue;
            while(que.size()>0){
                int node = que.front();
                que.pop_front();
                result.push_back(node);

                for(int nextNode : graph[node]){
                    inDegMapper[nextNode]--;
                    if(inDegMapper[nextNode]==0){
                        nextQue.push_back(nextNode);
                    }
                }
            }
            que = nextQue;
        }
        return  result.size()==n?semesters:-1;
    }
};
```



### As Far from Land as Possible (1911):

```cpp
#include<list>
class Solution {
public:
    /**
     * @param grid: An array.
     * @return: An integer.
     */
    bool canVisit(pair<int,int> node, vector<vector<int>> &grid){
        if(node.first<0 || node.first>=grid.size()){
            return false;
        }
        if(node.second<0 || node.second>=grid[node.first].size()){
            return false;
        }
        return grid[node.first][node.second]==0;
    }

    int maxDistance(vector<vector<int>> &grid) {
        // Write your code here.
        list<pair<pair<int,int>,int>> que;
        for(int i=0;i<grid.size();i++){
            for(int j=0;j<grid[i].size();j++){
                if(grid[i][j]==1){
                    que.push_back(make_pair(make_pair(i,j),1));
                }
            }
        }
        while(que.size()>0){
            pair<int,int> node = que.front().first;
            int currDist = que.front().second;
            que.pop_front();
            // cout<<node.first<<","<<node.second<<": ";

            pair<int,int> nextNode = make_pair(node.first-1, node.second);
            if(canVisit(nextNode, grid)){
                que.push_back(make_pair(nextNode, currDist+1));
                grid[nextNode.first][nextNode.second] = currDist+1;
                // cout<<"("<<nextNode.first<<","<<nextNode.second<<")";
            }
            nextNode = make_pair(node.first+1, node.second);
            if(canVisit(nextNode, grid)){
                que.push_back(make_pair(nextNode, currDist+1));
                grid[nextNode.first][nextNode.second] = currDist+1;
                // cout<<"("<<nextNode.first<<","<<nextNode.second<<")";
            }
            nextNode = make_pair(node.first, node.second-1);
            if(canVisit(nextNode, grid)){
                que.push_back(make_pair(nextNode, currDist+1));
                grid[nextNode.first][nextNode.second] = currDist+1;
                // cout<<"("<<nextNode.first<<","<<nextNode.second<<")";
            }
            nextNode = make_pair(node.first, node.second+1);
            if(canVisit(nextNode, grid)){
                que.push_back(make_pair(nextNode, currDist+1));
                grid[nextNode.first][nextNode.second] = currDist+1;
                // cout<<"("<<nextNode.first<<","<<nextNode.second<<")";
            }
            // cout<<endl;
        }

        int maxVal = -1;
        for(int i=0;i<grid.size();i++){
            for(int j=0;j<grid[i].size();j++){
                // cout<<grid[i][j]<<" ";
                if(grid[i][j]>1){
                    maxVal = max(maxVal, grid[i][j]-1);
                }
            }
            // cout<<endl;
        }
        return maxVal;
    }
};
```



### Maximum Width of Binary Tree (1101):
- Trick question on binary search

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
class Solution {
public:
    /**
     * @param root: the root
     * @return: the maximum width of the given tree
     */
    

    int widthOfBinaryTree(TreeNode *root) {
        // Write your code here3

        int maxWidth = 0;
        list<pair<TreeNode*,int>> que;
        if(root){
            que.push_back(make_pair(root, 0));
        }
        while(que.size()>0){
            list<pair<TreeNode*,int>> newQue;
            int leftMostIndex=-1, rightMostIndex=-1;
            while(que.size()>0){
                TreeNode *node = que.front().first;
                int currIndex = que.front().second;
                que.pop_front();
                // cout<<"exploring node: "<<node->val<<endl;

                if(leftMostIndex==-1){
                    leftMostIndex = currIndex;
                }
                rightMostIndex = currIndex;

                if(node->left){
                    newQue.push_back(make_pair(node->left, 2*currIndex+1));
                }
                if(node->right){
                    newQue.push_back(make_pair(node->right, 2*currIndex+2));
                }
            }

            maxWidth = max(maxWidth, rightMostIndex-leftMostIndex+1);
            que = newQue;
        }
        return maxWidth;
    }
};
```



### Push Dominoes (1431):

```cpp
#include <list>
#include <set>
class Solution {
public:
    /**
     * @param dominoes: a string
     * @return: a string representing the final state
     */
    string pushDominoes(string &dominoes) {
        // Write your code here
        list<int> que;
        set<int> visitedNodes;
        for(int i=0;i<dominoes.size();i++){
            if(dominoes.at(i)!='.'){
                que.push_back(i);
                visitedNodes.insert(i);
            }
        }

        while(que.size()>0){
            string str = dominoes;
            list<int> nextQue;

            while(que.size()>0){
                int index = que.front();
                que.pop_front();
                // cout<<"exploring node:"<<index<<" with val:"<<str<<endl;

                if(dominoes.at(index)=='L' && index>0 && dominoes.at(index-1)=='.'){
                    if(index>1 && dominoes.at(index-2)=='R'){
                        // don't do anything
                    } else {
                        str[index-1] = 'L';
                        nextQue.push_back(index-1);
                    }
                } else if(dominoes.at(index)=='R' && index<dominoes.size()-1 && dominoes.at(index+1)=='.'){
                    if(index<dominoes.size()-2 && dominoes.at(index+2)=='L'){
                        // don't do anything
                    } else {
                        str[index+1] = 'R';
                        nextQue.push_back(index+1);
                    }
                }
                
            }

            que = nextQue;
            dominoes = str;
            
        }

        return dominoes;
    }
};
```



### The Maze II (788):

```cpp
#include <list>
#include <queue>
#include <set>
class Solution {
public:
    /**
     * @param maze: the maze
     * @param start: the start
     * @param destination: the destination
     * @return: the shortest distance for the ball to stop at the destination
     */
    bool canVisit(pair<int,int> node, vector<vector<int>> &board){
        if(node.first<0 || node.first>=board.size()){
            return false;
        }
        if(node.second<0 || node.second>=board[node.first].size()){
            return false;
        }
        if(board[node.first][node.second]==1){
            return false;
        }
        return true;
    }

    pair<int,int> moveDirection(pair<int,int> position, vector<vector<int>> &maze, int dx, int dy){
        pair<int,int> finalPosition = position;
        while(true){
            pair<int,int> nextPosition = make_pair(finalPosition.first+dx, finalPosition.second+dy);
            if(!canVisit(nextPosition, maze)){
                break;
            }
            finalPosition = nextPosition;
        }
        return finalPosition;
    }

    int findDistance(pair<int,int> node1, pair<int,int> node2){
        return abs(node1.first-node2.first) + abs(node1.second-node2.second);
    }

    int shortestDistance(vector<vector<int>> &maze, vector<int> &start, vector<int> &destination) {
        // write your code here
        // list<pair<pair<int,int>,int>> que;
        priority_queue<pair<int, pair<int,int>>, vector<pair<int, pair<int,int>>>, greater<pair<int, pair<int,int>>>> que;
        set<pair<int,int>> visitedNodes;
        pair<int,int> startNode=make_pair(start[0],start[1]), targetNode=make_pair(destination[0],destination[1]);
        if(canVisit(startNode, maze)){
            que.push(make_pair(0, startNode));
            visitedNodes.insert(startNode);
        }
        while(que.size()>0){
            pair<int,int> node = que.top().second;
            int currDist = que.top().first;
            que.pop();
            visitedNodes.insert(node);
            // cout<<"exploring node:("<<node.first<<","<<node.second<<") with dist:"<<currDist<<endl;

            if(node == targetNode){
                return currDist;
            }

            pair<int,int> nextNode = moveDirection(node, maze, -1, 0);
            if(visitedNodes.find(nextNode) == visitedNodes.end()){
                int distance = findDistance(node, nextNode);
                que.push(make_pair(currDist+distance, nextNode));
            }
            nextNode = moveDirection(node, maze, 1, 0);
            if(visitedNodes.find(nextNode) == visitedNodes.end()){
                int distance = findDistance(node, nextNode);
                que.push(make_pair(currDist+distance, nextNode));
            }
            nextNode = moveDirection(node, maze, 0, -1);
            if(visitedNodes.find(nextNode) == visitedNodes.end()){
                int distance = findDistance(node, nextNode);
                que.push(make_pair(currDist+distance, nextNode));
            }
            nextNode = moveDirection(node, maze, 0, 1);
            if(visitedNodes.find(nextNode) == visitedNodes.end()){
                int distance = findDistance(node, nextNode);
                que.push(make_pair(currDist+distance, nextNode));
            }
        }
        return -1;
    }
};
```



### Serialize and Deserialize Binary Tree (7):

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
#include <sstream>
class Solution {
public:
    /**
     * This method will be invoked first, you should design your own algorithm 
     * to serialize a binary tree which denote by a root node to a string which
     * can be easily deserialized by your own "deserialize" method later.
     */
    string serialize(TreeNode * root) {
        // write your code here
        if(!root){
            return "#";
        }
        string str = to_string(root->val) + "," + serialize(root->left) + "," + serialize(root->right);
        // cout<<str<<endl;
        return str;
    }

    /**
     * This method will be invoked second, the argument data is what exactly
     * you serialized at method "serialize", that means the data is not given by
     * system, it's given by your own serialize method. So the format of data is
     * designed by yourself, and deserialize it here as you serialize it in 
     * "serialize" method.
     */
    TreeNode* deserialize(string &data) {
        // write your code here
        stringstream ss(data); // Create a stringstream from the input string
        string token;
        list<string> tokens;
        while (getline(ss, token, ',')) {
            tokens.push_back(token); // Add each token to the vector
        }

        return generateTree(tokens);
    }

    TreeNode* generateTree(list<string> &tokens){
        if(tokens.size()==0){
            return NULL;
        }
        string val = tokens.front();
        tokens.pop_front();
        if(val=="#"){
            return NULL;
        }
        TreeNode *node = new TreeNode(stoi(val));
        node->left = generateTree(tokens);
        node->right = generateTree(tokens);
        return node;
    }
};
```



###  Shortest Path in Undirected Graph (814):

```cpp
/**
 * Definition for undirected graph.
 * struct UndirectedGraphNode {
 *     int label;
 *     vector<UndirectedGraphNode *> neighbors;
 *     UndirectedGraphNode(int x) : label(x) {};
 * };
 */
#include <list>
#include <set>

class Solution {
public:
    /**
     * @param graph: a list of Undirected graph node
     * @param A: nodeA
     * @param B: nodeB
     * @return:  the length of the shortest path
     */
    int shortestPath(vector<UndirectedGraphNode*> graph, UndirectedGraphNode* A, UndirectedGraphNode* B) {
        // Write your code here
        list<pair<UndirectedGraphNode*,int>> que;
        set<UndirectedGraphNode*> visitedNodes;
        que.push_back(make_pair(A,0));
        
        while(que.size()>0){
            UndirectedGraphNode* node = que.front().first;
            int currDist = que.front().second;
            que.pop_front();

            if(node == B){
                return currDist;
            }
            if(visitedNodes.find(node) != visitedNodes.end()){
                continue;
            }
            visitedNodes.insert(node);

            for(UndirectedGraphNode* nextNode : node->neighbors){
                if(nextNode && visitedNodes.find(nextNode)==visitedNodes.end()){
                    que.push_back(make_pair(nextNode, currDist+1));
                }
            }
        }
        return -1;
    }
};
```



###  Shortest Path in Binary Matrix (3879):
- Preferred implementation of BFS

```cpp
#include <list>
#include <set>
#include <vector>
class Solution {
public:
    /**
     * @param grid: A two-dimensional array
     * @return: Length of shortest path in binary matrix
     */
    bool canVisit(pair<int,int> node, vector<vector<int>> &board){
        if(node.first<0 || node.first>=board.size()){
            return false;
        }
        if(node.second<0 || node.second>=board[node.first].size()){
            return false;
        }
        if(board[node.first][node.second]!=0){
            return false;
        }
        return true;
    }

    int shortestPathBinaryMatrix(vector<vector<int>> &board) {
        // write your code here
        pair<int,int> start={0,0}, end={board.size()-1, board[board.size()-1].size()-1};
        vector<pair<int,int>> dirVec = {{-1,0},{-1,1},{-1,-1}, {0,1},{0,-1}, {1,0},{1,1},{1,-1}};
        list<pair<pair<int,int>,int>> que;
        set<pair<int,int>> visitedNodes;
        if(canVisit(start, board)){
            que.push_back({start,1});
        }
        while(que.size()>0){
            pair<int,int> node = que.front().first;
            int currDist = que.front().second;
            que.pop_front();

            if(node == end){
                return currDist;
            }
            if(visitedNodes.find(node) != visitedNodes.end()){
                continue;
            }
            visitedNodes.insert(node);

            for(const pair<int,int> &dir : dirVec){
                pair<int,int> nextNode = {node.first+dir.first, node.second+dir.second};
                if(canVisit(nextNode, board)){
                    que.push_back({nextNode, currDist+1});
                }
            }
        }
        return -1;
    }
};
```



### Minimum Path Sum II (1582):
- Preferred implementation of Dijkstra's shortet path

```cpp
#include <vector>
#include <set>
#include <queue>
class Solution {
public:
    /**
     * @param matrix: a matrix
     * @return: the minimum height
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

    int minPathSumII(vector<vector<int>> &board) {
        // Write your code here
        if(board.size()==0){
            return -1;
        }
        vector<pair<int,int>> dirArray = {{-1,0},{1,0},{0,-1},{0,1}};
        priority_queue< pair<int,pair<int,int>>, vector<pair<int,pair<int,int>>>, greater<pair<int,pair<int,int>>> > que;
        pair<int,int> start={board.size()-1,0}, end={0,board[0].size()-1};
        set<pair<int,int>> visitedNodes;
        if(canVisit(start, board)){
            que.push({board[start.first][start.second], start});
        }

        while(que.size()>0){
            pair<int,int> node = que.top().second;
            int currDist = que.top().first;
            que.pop();

            if(node==end){
                return currDist;
            }
            if(visitedNodes.find(node) != visitedNodes.end()){
                continue;
            }
            visitedNodes.insert(node);
            for(const pair<int,int> &dir : dirArray){
                pair<int,int> nextNode = {node.first+dir.first, node.second+dir.second};
                if(canVisit(nextNode, board)){
                    que.push({currDist+board[nextNode.first][nextNode.second], nextNode});
                }
            }
        }
        return -1;
    }
};
```
