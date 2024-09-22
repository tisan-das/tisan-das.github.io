---
layout: post
title: Binary Tree Algorithms - Part II
published: true
---

This wiki contains a couple of well-defined problems on Binary Tree.


#### Delete Node in a Linked List (372):

```cpp
    void deleteNode(ListNode * node) {
        // Assumption: node is not head or tail
        while(node && node->next && node->next->next){
            node->val = node->next->val;
            node = node->next;
        }
        if (node && node->next){
            node->val = node->next->val;
            ListNode *endNode = node->next;
            node->next = NULL;
            delete endNode;
        }
    }
```



### Construct Binary Tree from Preorder and Inorder Traversal (73):

```cpp
    TreeNode* buildTree(vector<int> &preorder, vector<int> &inorder) {
        // write your code here
        int preorderIndex=0;
        return buildTree(preorder, preorderIndex, inorder, 0, inorder.size()-1);
    }

    TreeNode* buildTree(vector<int> &preorder, int &preIndex, vector<int> &inorder, int inStartIndex, int inEndIndex){
        if(preIndex >= preorder.size()){
            return NULL;
        }
        if(inStartIndex > inEndIndex){
            return NULL;
        }
        int value = preorder[preIndex];
        TreeNode* node = new TreeNode(value);
        preIndex++;
        int index = inStartIndex;
        while(index <= inEndIndex && inorder[index]!=value){
            index++;
        }
        node->left = buildTree(preorder, preIndex, inorder, inStartIndex, index-1);
        node->right = buildTree(preorder, preIndex, inorder, index+1, inEndIndex);
        return node;
    }
```



### Construct Binary Tree from Inorder and Postorder Traversal (72):

```cpp
    TreeNode* buildTree(vector<int> &inorder, vector<int> &postorder) {
        // write your code here
        int postIndex = postorder.size()-1;
        return buildTree(postorder, postIndex, inorder, 0, inorder.size()-1);
    }

    TreeNode* buildTree(vector<int> &postorder, int &postIndex, vector<int> &inorder, int inStartIndex, int inEndIndex){
        if(postIndex<0 || postIndex >= postorder.size()){
            return NULL;
        }
        if(inStartIndex > inEndIndex){
            return NULL;
        }
        int value = postorder[postIndex];
        TreeNode *node = new TreeNode(value);
        postIndex--;
        int index = inStartIndex;
        while(index>=0 && inorder[index]!=value){
            index++;
        }
        //cout<<value<<","<<inStartIndex<<","<<index<<","<<inEndIndex<<endl;
        node->right = buildTree(postorder, postIndex, inorder, index+1, inEndIndex);
        node->left = buildTree(postorder, postIndex, inorder, inStartIndex, index-1);
        return node;
    }
```



### Binary Tree Maximum Path Sum (94):

```cpp
    int maxPathSum(TreeNode *root) {
        // write your code here
        if(!root){
            return 0;
        }
        int maxWeight = -9999999;
        maxPathSum(root, maxWeight);
        return maxWeight;
    }

    int maxPathSum(TreeNode *root, int &maxWeight){
        if(!root){
            return -9999999;
        }
        int leftSum = maxPathSum(root->left, maxWeight);
        int rightSum = maxPathSum(root->right, maxWeight);
        maxWeight = max(maxWeight, root->val+leftSum+rightSum);
        maxWeight = max(maxWeight, root->val);
        maxWeight = max(maxWeight, root->val+max(leftSum, rightSum));
        maxWeight = max(maxWeight, max(leftSum, rightSum));
        //cout<<root->val<<":"<<leftSum<<","<<rightSum<<"|"<<maxWeight<<endl;
        return max(root->val+max(leftSum, rightSum), root->val);
    }
```



### Trim a Binary Search Tree (701):

Given the root of a binary search tree and 2 numbers min and max, trim the tree such that all the numbers in the new tree are between min and max (inclusive).

```cpp
    TreeNode* trimBST(TreeNode *root, int minimum, int maximum) {
        // write your code here
        if(!root){
            return NULL;
        }
        if(root->val < minimum){
            root = trimBST(root->right, minimum, maximum);
        } else if(root->val > maximum){
            root = trimBST(root->left, minimum, maximum);
        }
        if(root){
            root->left = trimBST(root->left, minimum, maximum);
            root->right = trimBST(root->right, minimum, maximum);
        }
        return root;
    }
```



### Sum Root to Leaf Numbers (1353):

```cpp
    int sumNumbers(TreeNode *root) {
        // write your code here
        vector<int> array;
        int sum;
        sumNumbers(root, array, sum);
        return sum;
    }

    void sumNumbers(TreeNode* root, vector<int> &path, int &totalSum){
        if(!root){
            return;
        }
        path.push_back(root->val);
        if(!root->left && !root->right){
            // calc total sum
            totalSum += pathToInt(path);
            // cout<<"val:"<<root->val<<" totalSum:"<<totalSum<<endl;
            path.pop_back();    
            return;
        }
        sumNumbers(root->left, path, totalSum);
        sumNumbers(root->right, path, totalSum);
        path.pop_back();
    }
```



### Verify Preorder Sequence in Binary Search Tree (1307):

Given an array of numbers, verify whether it is the correct preorder traversal sequence of a binary search tree.

You may assume each number in the sequence is unique.

Follow up:
Could you do it using only constant space complexity?

```cpp
    bool verifyPreorder(vector<int> &preorder) {
        // write your code here
        return verifyPreorder(preorder , 0, preorder.size()-1);
    }

    bool verifyPreorder(vector<int> &preorder, int startIndex, int endIndex){
        // cout<<"entry start:"<<startIndex<<"end:"<<endIndex<<endl;
        if(startIndex >= endIndex){
            return true;
        }
        int pivot = preorder[startIndex];
        int splitIndex = startIndex+1;
        while(splitIndex<=endIndex && preorder[splitIndex]<pivot){
            splitIndex++;
        }
        // cout<<"split:"<<splitIndex<<endl;
        for(int i=splitIndex;i<=endIndex;i++){
            if(preorder[i] <pivot){
                // cout<<"false:"<<i<<endl;
                return false;
            }
        }

        return verifyPreorder(preorder, startIndex+1, splitIndex-1) &&
            verifyPreorder(preorder, splitIndex, endIndex);
    }
```



### Equal Tree Partition (864):

Given a binary tree with n nodes, your task is to check if it's possible to partition the tree to two trees which have the equal sum of values after removing exactly one edge on the original tree.

```cpp
    bool checkEqualTree(TreeNode *root) {
        // write your code here
        int sum = sumOfNodes(root);
        // cout<<"sum:"<<sum<<endl;
        if(sum%2==1){
            return false;
        }
        return isSumSubTree(root, sum/2, sum/2);
    }

    bool isSumSubTree(TreeNode* root, int remSum, int totalSum){
        if(!root && remSum==0){
            // cout<<"ret: true"<<endl;
            return true;
        }
        if(!root){
            // cout<<"ret: false"<<endl;
            return false;
        }
        // cout<<"mid:"<<root->val<<" ,remSum:"<<remSum<<endl;
        if(!root->right && !root->left){
            return root->val==remSum;
        }
        return isSumSubTree(root->left, remSum-root->val, totalSum) || 
            isSumSubTree(root->right, remSum-root->val, totalSum) ||
            isSumSubTree(root->left, totalSum, totalSum) || 
            isSumSubTree(root->right, totalSum, totalSum);
    }

    int sumOfNodes(TreeNode* root){
        if(!root){
            return 0;
        }
        return root->val + sumOfNodes(root->left) + sumOfNodes(root->right);
    }
```



### Fix Binary Search Tree (3600):

Given the root of a binary tree where exactly two nodes have been swapped.

Please identify the nodes and swap them back in order to recover the original binary search tree. You should try to do this without changing the structure of the tree. Finally, return it.

```cpp
    TreeNode* fixBST(TreeNode *root) {
        // --- write your code here ---
        vector<TreeNode*> traversal;
        inorderTraversal(root, traversal);
        int invalidIndex=0, swappedIndex=0;
        
        // cout<<"inorder: ";
        // for(int i=0;i<traversal.size();i++){
        //     cout<<traversal[i]->val<<",";
        // }
        // cout<<endl;

        vector<int> values;
        for(int i=0;i<traversal.size();i++){
            values.push_back(traversal[i]->val);
        }
        sort(values.begin(), values.end());

        for(int i=0;i<traversal.size();i++){
            traversal[i]->val = values[i];
        }

        return root;
    }

    void inorderTraversal(TreeNode* root, vector<TreeNode*> &traversal){
        if(!root){
            return;
        }
        inorderTraversal(root->left, traversal);
        traversal.push_back(root);
        inorderTraversal(root->right, traversal);
    }
```



### Inorder Successor in BST II (3665):

There exists a binary search tree, and the binary tree node holds its parent node parent.

In this question, you will get any node of the binary search tree. You need to return the node after this node in the inorder traversal order, or null if there is no successor node.

```cpp
    ParentTreeNode* inorderSuccessor(ParentTreeNode *node) {
        // write your code here
        if(node->right){
            node = node->right;
            while(node->left){
                node = node->left;
            }
            return node;
        } else{
            while(node->parent && node->parent->right == node){
                node = node->parent;
            }
            return node->parent;
        }
    }
```



### Count Univalue Subtrees (921):

Given a binary tree, count the number of uni-value subtrees.

A Uni-value subtree means all nodes of the subtree have the same value.

```cpp
    int countUnivalSubtrees(TreeNode *root) {
        // write your code here
        int count = 0;
        isUnivalueSubtree(root, count);
        return count;
    }

    bool isUnivalueSubtree(TreeNode *root, int &counter){
        if(!root){
            return true;
        }
        bool leftVal = isUnivalueSubtree(root->left, counter);
        bool rightVal = isUnivalueSubtree(root->right, counter);
        if (!leftVal || !rightVal){
            return false;
        }
        if(root->left && root->val != root->left->val){
            return false;
        }
        if(root->right && root->val != root->right->val){
            return false;
        }
        counter++;
        return true;
    }
```



### Construct Binary Tree from Preorder and Postorder Traversal (1593):

```cpp
    TreeNode* constructFromPrePost(vector<int> &pre, vector<int> &post) {
        return constructTree(pre, post, 0, pre.size()-1, 0, post.size()-1);
    }

    TreeNode* constructTree(vector<int> &pre, vector<int> &post, int preStart, int preEnd, int postStart, int postEnd){
        if(preStart > preEnd){
            return NULL;
        }
        TreeNode* node = new TreeNode(pre[preStart]);
        if(preStart == preEnd){
            return node;
        }
        // cout<<"preStart:"<<preStart<<" preEnd:"<<preEnd<<" postStart:"<<postStart<<" postEnd:"<<postEnd<<endl;
        int preNext = preStart+1;
        int postPivot = postStart;
        for(int i=postStart;i<postEnd;i++){
            if(post[i] == pre[preNext]){
                postPivot = i;
                break;
            }
        }
        // cout<<"postPivot: "<<postPivot<<endl;
        // what if this one is not found?
        node->left = constructTree(pre,post,preStart+1,preStart+1+postPivot-postStart, postStart, postPivot);
        node->right = constructTree(pre,post,preStart+1+(postPivot-postStart+1),preEnd, postPivot+1, postEnd);
        return node;
    }
```

