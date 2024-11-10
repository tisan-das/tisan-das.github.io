---
layout: post
title: Union-Find Problem Sets
published: true
---

This wiki contains a couple of well-defined problems solved via Union-Find data structure.


### Graph Valid Tree (178):

```cpp
    int find(vector<int> &parent, int index){
        int root = index;
        while(parent[root] != root){
            root = parent[root];
        }
        return root;
    }

    void unionSet(vector<int> &parent,vector<int> &rank, int index1, int index2){
        int root1 = find(parent, index1);
        int root2 = find(parent, index2);
        if (rank[root1] < rank[root2]){
            parent[root1] = root2;
        } else if(rank[root1] > rank[root2]){
            parent[root2] = root1;
        } else {
            parent[root1] = root2;
            rank[root2]++; 
        }
    }

    bool validTree(int n, vector<vector<int>> &edges) {
        // write your code here
        vector<int> parent(n), rank(n,0);
        for(int i=0;i<n;i++){
            parent[i] = i;
        }
        for(int i=0;i<edges.size();i++){
            int node1=edges[i][0], node2=edges[i][1];
            int root1 = find(parent, node1);
            int root2 = find(parent, node2);
            if(root1 == root2){
                return false;
            }
            unionSet(parent, rank, node1, node2);
        }
        int rootNodes=0;
        for(int i=0;i<parent.size();i++){
            if(parent[i] == i){
                rootNodes++;
            }
        }
        if(rootNodes>1){
            cout<<"false root:"<<rootNodes<<endl;
            return false;
        }
        return true;
    }
```



### Number of Islands II (434):

```cpp
    pair<int,int> findRoot(pair<int,int> node){
        pair<int,int> root = node;
        while(parentMap.find(root) != parentMap.end()){
            root = parentMap[root];
        }
        return root;
    }

    void unionSets(pair<int,int> index1, pair<int,int> index2){
        pair<int,int> root1 = findRoot(index1);
        pair<int,int> root2 = findRoot(index2);

        if(root1 == root2){
            return;
        }if(rankMap[root1] < rankMap[root2]){
            parentMap[root1] = root2;
        } else if(rankMap[root1] > rankMap[root2]){
            parentMap[root2] = root1;
        } else {
            parentMap[root1] = root2;
            rankMap[root2]++;
        }
        groups--;
    }

    vector<int> numIslands2(int n, int m, vector<Point> &operators) {
        // write your code here
        parentMap.clear();
        rankMap.clear();
        groups = 0;
        set<pair<int,int>> visitedPairSet;
        vector<int> groupArray;

        for(int i=0;i<operators.size();i++){
            pair<int,int> node = make_pair(operators[i].x, operators[i].y);
            if(visitedPairSet.find(node) != visitedPairSet.end()){
                groupArray.push_back(groups);
                continue;
            }
            groups++;
            if(visitedPairSet.find( make_pair(node.first-1,node.second) ) != visitedPairSet.end() ){
                unionSets(node, make_pair(node.first-1,node.second) );
            }
            if(visitedPairSet.find( make_pair(node.first+1,node.second) ) != visitedPairSet.end() ){
                unionSets(node, make_pair(node.first+1,node.second) );
            }
            if(visitedPairSet.find( make_pair(node.first,node.second-1) ) != visitedPairSet.end() ){
                unionSets(node, make_pair(node.first,node.second-1) );
            }
            if(visitedPairSet.find( make_pair(node.first,node.second+1) ) != visitedPairSet.end() ){
                unionSets(node, make_pair(node.first,node.second+1) );
            }
            visitedPairSet.insert(node);
            groupArray.push_back(groups);
        }
        return groupArray;
    }

    private:
        map<pair<int,int>, pair<int,int>> parentMap;
        map<pair<int,int>, int> rankMap;
        int groups;
```



### Accounts Merge (1070):

```cpp
    int findRoot(vector<int> &parentArray, int index){
        int root = index;
        while(parentArray[root] != root){
            root = parentArray[root];
        }
        return root;
    }

    void unionSets(vector<int> &parentArray, vector<int> &rankArray, int index1, int index2){
        int root1 = findRoot(parentArray, index1);
        int root2 = findRoot(parentArray, index2);
        if(root1 == root2){
            return;
        }
        // cout<<"merge2: "<<index1<<","<<index2<<":"<<root1<<","<<root2<<endl;
        if(rankArray[root1] > rankArray[root2]){
            parentArray[root2] = root1;
        } else if(rankArray[root2] > rankArray[root1]){
            parentArray[root1] = root2;
        } else {
            parentArray[root2] = root1;
            rankArray[root1]++;
        }
    }

    vector<vector<string>> accountsMerge(vector<vector<string>> &accounts) {
        // write your code here
        vector<int> parentArray(accounts.size()), rankArray(accounts.size(),0);
        for(int i=0;i<parentArray.size();i++){
            parentArray[i] = i;
        }


        map<string, int> emailMapper;
        for(int i=0;i<accounts.size();i++){
            string accOwner = accounts[i][0];
            for(int j=1;j<accounts[i].size();j++){
                if(emailMapper.find(accounts[i][j]) != emailMapper.end()){
                    // cout<<"merging "<<i<<" with "<<emailMapper[accounts[i][j]]<<" for "<<accounts[i][j]<<endl;
                    unionSets(parentArray, rankArray, i, emailMapper[accounts[i][j]]);
                } else {
                    emailMapper[accounts[i][j]] = i;
                }
            }
        }

        map<int, set<string>> mergedMapper;
        for(int i=0;i<accounts.size();i++){
            int root = findRoot(parentArray, i);
            // cout<<"root of index "<<i<<" : "<<root<<endl;
            for(int j=1;j<accounts[i].size();j++){
                mergedMapper[root].insert(accounts[i][j]);
            }
        }
        vector<vector<string>> result;
        for(auto const &pr : mergedMapper){
            vector<string> arr;
            arr.push_back(accounts[pr.first][0]);
            for(const string &str : pr.second){
                arr.push_back(str);
            }
            result.push_back(arr);
        }
        return result;
    }
```



### Maximum Connected Area (261):

```cpp
    pair<int,int> findRoot(pair<int,int> index){
        pair<int,int> root = index;
        while(parentMap.find(root) != parentMap.end()){
            root = parentMap[root];
        }
        return root;
    }

    void mergeSet(pair<int,int> index1, pair<int,int> index2){
        // cout<<"merging indexs1 : ("<<index1.first<<","<<index1.second<<") ("<<index2.first<<","<<index2.second<<")"<<endl;
        pair<int,int> root1=findRoot(index1), root2=findRoot(index2);
        int rank1=rankMap[root1], rank2=rankMap[root2];

        if(root1==root2){
            return;
        }
        // cout<<"merging indexs2 : ("<<root1.first<<","<<root1.second<<") ("<<root2.first<<","<<root2.second<<")"<<endl;
        if(rank1 > rank2){
            parentMap[root2] = root1;
            groupSizeMap[root1] += groupSizeMap[root2];
        } else if(rank1 < rank2){
            parentMap[root1] = root2;
            groupSizeMap[root2] += groupSizeMap[root1];
        } else {
            parentMap[root2] = root1;
            groupSizeMap[root1] += groupSizeMap[root2];
            rankMap[root1]++;
        }
    }

    bool isValid(vector<vector<int>> &grid, int i,int j){
        if(i<0 || i>=grid.size()){
            return false;
        }
        if(j<0 || j>=grid[i].size()){
            return false;
        }
        if(grid[i][j] != 1){
            return false;
        }
        return true;
    }

    int maxArea(vector<vector<int>> &matrix) {
        // write your code here.
        parentMap.clear();
        rankMap.clear();
        groupSizeMap.clear();

        for(int i=0;i<matrix.size();i++){
            for(int j=0;j<matrix[i].size();j++){
                if(matrix[i][j] == 1){
                    groupSizeMap[make_pair(i,j)] = 1;
                }
            }
        }

        for(int i=0;i<matrix.size();i++){
            for(int j=0;j<matrix[i].size();j++){
                if(matrix[i][j] != 1){
                    continue;
                }
                pair<int,int> node = make_pair(i,j);
                // cout<<"checking for node: ("<<i<<","<<j<<")"<<endl;
                if(isValid(matrix, node.first-1, node.second)){
                    mergeSet(node, make_pair(node.first-1, node.second));
                }
                if(isValid(matrix, node.first+1, node.second)){
                    mergeSet(node, make_pair(node.first+1, node.second));
                }
                if(isValid(matrix, node.first, node.second-1)){
                    mergeSet(node, make_pair(node.first, node.second-1));
                }
                if(isValid(matrix, node.first, node.second+1)){
                    mergeSet(node, make_pair(node.first, node.second+1));
                }
            }
        }

        int maxArea = 0;
        for(int i=0;i<matrix.size();i++){
            for(int j=0;j<matrix[i].size();j++){
                // cout<<"calc current area with index:"<<i<<","<<j<<": "<<endl;
                int area = 1;
                if(matrix[i][j] == 1){
                    pair<int,int> root = findRoot(make_pair(i,j));
                    area = groupSizeMap[root];
                } else {
                    set<pair<int,int>> visitedRootSet;
                    if(isValid(matrix, i-1, j)){
                        pair<int,int> root = findRoot(make_pair(i-1,j));
                        if(visitedRootSet.find(root) == visitedRootSet.end()){
                            visitedRootSet.insert(root);
                            area += groupSizeMap[root];
                            // cout<<"1:"<<area<<endl;
                        }
                    }
                    if(isValid(matrix, i+1, j)){
                        pair<int,int> root = findRoot(make_pair(i+1,j));
                        if(visitedRootSet.find(root) == visitedRootSet.end()){
                            visitedRootSet.insert(root);
                            area += groupSizeMap[root];
                            // cout<<"2:"<<area<<endl;
                        }
                    }
                    if(isValid(matrix, i, j-1)){
                        pair<int,int> root = findRoot(make_pair(i,j-1));
                        if(visitedRootSet.find(root) == visitedRootSet.end()){
                            visitedRootSet.insert(root);
                            area += groupSizeMap[root];
                            // cout<<"3:"<<area<<endl;
                        }
                    }
                    if(isValid(matrix, i, j+1)){
                        pair<int,int> root = findRoot(make_pair(i,j+1));
                        if(visitedRootSet.find(root) == visitedRootSet.end()){
                            visitedRootSet.insert(root);
                            area += groupSizeMap[root];
                            // cout<<"4:"<<area<<endl;
                        }
                    }
                }
                // cout<<"current area with index:"<<i<<","<<j<<": "<<area<<endl;
                maxArea = max(maxArea, area);
            }
        }
        return maxArea;
    }

    private:
        map<pair<int,int>, pair<int,int>> parentMap;
        map<pair<int,int>, int> rankMap;
        map<pair<int,int>, int> groupSizeMap;
```



### Making A Large Island (1391):

```cpp
    pair<int,int> findRoot(pair<int,int> index){
        pair<int,int> root = index;
        while(parentMap.find(root) != parentMap.end()){
            root = parentMap[root];
        }
        return root;
    }

    void mergeSet(pair<int,int> index1, pair<int,int> index2){
        // cout<<"merging index1: ("<<index1.first<<","<<index1.second<<") ("<<index2.first<<","<<index2.second<<")"<<endl;
        pair<int,int> root1=findRoot(index1), root2=findRoot(index2);
        int rank1=rankMap[root1], rank2=rankMap[root2];
        
        if(root1==root2){
            return;
        }
        // cout<<"merging index2: ("<<root1.first<<","<<root1.second<<") ("<<root2.first<<","<<root2.second<<")"<<endl;
        if(rank1 > rank2){
            parentMap[root2] = root1;
            groupSizeMap[root1] += groupSizeMap[root2];
        } else if(rank1 < rank2){
            parentMap[root1] = root2;
            groupSizeMap[root2] += groupSizeMap[root1];
        } else {
            parentMap[root2] = root1;
            groupSizeMap[root1] += groupSizeMap[root2];
            rankMap[root1]++; 
        }
    }

    bool isValid(vector<vector<int>> &grid, int i, int j){
        if(i<0 || i>=grid.size()){
            return false;
        }
        if(j<0 || j>=grid[i].size()){
            return false;
        }
        if(grid[i][j] != 1){
            return false;
        }
        return true;
    }


    int largestIsland(vector<vector<int>> &grid) {
        //
        parentMap.clear();
        rankMap.clear();
        groupSizeMap.clear();

        for(int i=0;i<grid.size();i++){
            for(int j=0;j<grid[i].size();j++){
                groupSizeMap[make_pair(i,j)] = grid[i][j];
            }
        }

        for(int i=0;i<grid.size();i++){
            for(int j=0;j<grid[i].size();j++){
                if(grid[i][j] != 1){
                    continue;
                }
                pair<int,int> node = make_pair(i,j);
                if(isValid(grid, node.first-1, node.second)){
                    mergeSet(node, make_pair(node.first-1,node.second));
                }
                if(isValid(grid, node.first+1, node.second)){
                    mergeSet(node, make_pair(node.first+1,node.second));
                }
                if(isValid(grid, node.first, node.second-1)){
                    mergeSet(node, make_pair(node.first,node.second-1));
                }
                if(isValid(grid, node.first, node.second+1)){
                    mergeSet(node, make_pair(node.first,node.second+1));
                }
            }
        }

        int maxArea = 0;
        for(int i=0;i<grid.size();i++){
            for(int j=0;j<grid[i].size();j++){
                // cout<<"checking for index: "<<i<<","<<j<<endl;
                int area = 1;
                set<pair<int,int>> visitedSet;
                if(grid[i][j]==1){
                    pair<int,int> root = findRoot(make_pair(i,j));
                    // cout<<"root index1 :"<<root.first<<","<<root.second<<endl;
                    area = groupSizeMap[root];
                } else {
                    if(isValid(grid, i-1, j)){
                        pair<int,int> root = findRoot(make_pair(i-1,j));
                        if(visitedSet.find(root) == visitedSet.end()){
                            visitedSet.insert(root);
                            area += groupSizeMap[root];
                        }
                    }

                    if(isValid(grid, i+1, j)){
                        pair<int,int> root = findRoot(make_pair(i+1,j));
                        if(visitedSet.find(root) == visitedSet.end()){
                            visitedSet.insert(root);
                            area += groupSizeMap[root];
                        }
                    }

                    if(isValid(grid, i, j-1)){
                        pair<int,int> root = findRoot(make_pair(i,j-1));
                        if(visitedSet.find(root) == visitedSet.end()){
                            visitedSet.insert(root);
                            area += groupSizeMap[root];
                        }
                    }

                    if(isValid(grid, i, j+1)){
                        pair<int,int> root = findRoot(make_pair(i,j+1));
                        if(visitedSet.find(root) == visitedSet.end()){
                            visitedSet.insert(root);
                            area += groupSizeMap[root];
                        }
                    }
                }

                maxArea = max(maxArea, area);
            }
        }
        return maxArea;
    }

    private:
        map<pair<int,int>, pair<int,int>> parentMap;
        map<pair<int,int>, int> rankMap, groupSizeMap; 
```



### Minimum Number of Visited Lattices in a Matrix (3709):

```cpp
    bool isValid(vector<vector<int>> &grid, int i, int j){
        if(i<0 || i>=grid.size()){
            return false;
        }
        if(j<0 || j>=grid[i].size()){
            return false;
        }
        return true;
    }

    int minimumVisitedLattices(vector<vector<int>> &grid) {
        // --- write your code here ---
        list<pair<pair<int,int>, int>> que;
        set<pair<int,int>> visitedNodeSet;
        que.push_back( make_pair( make_pair(0,0), 1));
        visitedNodeSet.insert(make_pair(0,0));

        while(que.size()!=0){
            pair<pair<int,int>, int> node = que.front();
            que.pop_front();
            // cout<<"exploring node: "<<node.first.first<<","<<node.first.second<<" : "<<node.second<<endl;
            if(node.first.first==grid.size()-1 && node.first.second==grid[grid.size()-1].size()-1){
                return node.second;
            }

            for(int i=1;i<=grid[node.first.first][node.first.second];i++){
                if(isValid(grid, node.first.first, node.first.second+i)){
                    if(visitedNodeSet.find(make_pair(node.first.first,node.first.second+i)) == visitedNodeSet.end()){
                        que.push_back( make_pair(make_pair(node.first.first,node.first.second+i), node.second+1) );
                        visitedNodeSet.insert(make_pair(node.first.first,node.first.second+i));
                        // cout<<"inserting node:"<<node.first.first<<","<<node.first.second+i<<endl;
                    }
                }

                if(isValid(grid, node.first.first+i, node.first.second)){
                    if(visitedNodeSet.find(make_pair(node.first.first+i,node.first.second)) == visitedNodeSet.end()){
                        que.push_back( make_pair(make_pair(node.first.first+i,node.first.second), node.second+1) );
                        visitedNodeSet.insert(make_pair(node.first.first+i,node.first.second));
                        // cout<<"inserting node:"<<node.first.first+i<<","<<node.first.second<<endl;
                    }
                }
            }
        }

        return -1;
    }
```



### The Minimum String After Swapping (3604):

```cpp
    int findRoot(int index){
        int root = index;
        while(parentArray[root] != -1){
            root = parentArray[root];
        }
        return root;
    }

    void mergeSet(int index1,int index2){
        int root1=findRoot(index1), root2=findRoot(index2);
        int rank1=rankArray[root1], rank2=rankArray[root2];

        if(root1 == root2){
            return;
        }
        if(rank1 > rank2){
            parentArray[root2] = root1;
        } else if(rank1 < rank2){
            parentArray[root1] = root2;
        } else {
            parentArray[root2] = root1;
            rankArray[root1]++;
        }
    }

    string minStringAfterSwap(string &s, vector<vector<int>> &pairs) {
        // // write your code here
        parentArray.resize(s.size(), -1);
        rankArray.resize(s.size(), 0);
        for(int i=0;i<pairs.size();i++){
            mergeSet(pairs[i][0], pairs[i][1]);
        }

        map<int, vector<char>> posMapper;
        for(int i=0;i<s.size();i++){
            int root = findRoot(i);
            posMapper[root].push_back(s.at(i));
        }

        for(auto &pr : posMapper){
            sort(pr.second.begin(), pr.second.end());
        }
        // for(auto const &pr: posMapper){
        //     cout<<"pr:"<<pr.first<<endl;
        //     for(int i=0;i<pr.second.size();i++){
        //         cout<<pr.second[i]<<",";
        //     }
        //     cout<<endl;
        // }
        map<int,int> posMapperIndexVisited;
        for(auto const &pr: posMapper){
            posMapperIndexVisited[pr.first] = -1;
        }
        string result = s;
        for(int i=0;i<s.size();i++){
            int root = findRoot(i);
            posMapperIndexVisited[root]++;
            result.at(i) = posMapper[root][posMapperIndexVisited[root]];
        }
        return result;
    }

    private:
        vector<int> parentArray,rankArray;
```



### Minimize Malware Spread (1718):

```cpp
    int findRoot(int index){
        int root = index;
        while(parentArray[root] != -1){
            root = parentArray[root];
        }
        return root;
    }

    void mergeSet(int index1, int index2){
        // cout<<"merging "<<index1<<","<<index2<<endl;
        int root1=findRoot(index1), root2=findRoot(index2);
        int rank1=rankArray[root1], rank2=rankArray[root2];

        if(root1 == root2){
            return;
        }
        // cout<<"merging roots "<<root1<<","<<root2<<endl;
        if(rank1 > rank2){
            parentArray[root2] = root1;
            groupSize[root1] += groupSize[root2];
        } else if(rank1 < rank2){
            parentArray[root1] = root2;
            groupSize[root2] += groupSize[root1];
        } else {
            parentArray[root2] = root1;
            groupSize[root1] += groupSize[root2];
            rankArray[root1]++;
        }
        //  cout<<"merged roots "<<root1<<","<<root2<<endl;
    }

    int minMalwareSpread(vector<vector<int>> &graph, vector<int> &initial) {
        // write your code here
        parentArray.resize(graph.size(), -1);
        rankArray.resize(graph.size(), 0);
        groupSize.resize(graph.size(), 1);

        for(int i=0;i<graph.size();i++){
            for(int j=0;j<graph[i].size();j++){
                if(graph[i][j] == 1){
                    // cout<<"going to merge: "<<i<<","<<j<<endl;
                    mergeSet(i,j);
                }
            }
        }

        sort(initial.begin(),initial.end());
        map<int,int> rootNodes;
        for(int i=0;i<initial.size();i++){
            int root = findRoot(initial[i]);
            rootNodes[root]++;
        }
        int maxConnectedIndex=0, maxConnectedArea=0;
        for(int i=0;i<initial.size();i++){
            int root = findRoot(initial[i]);
            if(rootNodes[root] > 1){
                continue;
            }
            if(groupSize[root] > maxConnectedArea){
                maxConnectedArea = groupSize[root];
                maxConnectedIndex = i;
            }
        }
        return initial[maxConnectedIndex];
    }

    private:
        vector<int> parentArray, rankArray, groupSize;
```


