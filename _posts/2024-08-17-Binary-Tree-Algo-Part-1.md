---
layout: post
title: Binary Tree Algorithms - Part I
published: true
---


#### Iterative Post-order Traversal (1783):

```cpp
    vector<int> postorderTraversalStack(TreeNode *root){
        vector<int> result;
        list<TreeNode*> stck1,stck2;
        if(!root){
            return result;
        }
        stck1.push_back(root);
        while(stck1.size()>0){
            TreeNode *node = stck1.back();
            stck1.pop_back();
            stck2.push_back(node);
            if(node->left){
                stck1.push_back(node->left);
            }
            if(node->right){
                stck1.push_back(node->right);
            }
        }
        while(stck2.size()>0){
            TreeNode *node = stck2.back();
            stck2.pop_back();
            result.push_back(node->val);
        }
        return result;
    }
```


#### Iterative Pre-order Traversal (66):

```cpp
    vector<int> preorderIterativeTraversal(TreeNode *root){
        list<TreeNode*> stck;
        vector<int> traversed;
        if(root){
            stck.push_back(root);
        }
        while(stck.size()>0){
            TreeNode *node = stck.back();
            stck.pop_back();
            if(node->right){
                stck.push_back(node->right);
            }
            if(node->left){
                stck.push_back(node->left);
            }
            traversed.push_back(node->val);
        }
        return traversed;
    }
```


### In-order Traversal (1746):

```cpp
    vector<int> inorderTraversal(TreeNode *root){
        vector<int> traversed;
        list<TreeNode*> stck;
        TreeNode *node = root;

        while(node || stck.size()>0){
            
            while(node){
                stck.push_back(node);
                node = node->left;
            }
            node = stck.back();
            stck.pop_back();
            traversed.push_back(node->val);
            node = node->right;
        }
        return traversed;
    }
```



### Lowest Common Ancestor in BST (1311):

```cpp
    TreeNode * lowestCommonAncestor(TreeNode * root, TreeNode * p, TreeNode * q) {
        // write your code here
        if(!root || !p || !q){
            return NULL;
        }
        TreeNode *node = root;
        while(true){
            if(p->val < node->val && q->val < node->val){
                node = node->left;
            } else if(p->val > node->val && q->val > node->val){
                node = node->right;
            } else {
                return node;
            }
        }
        return node;
    }
```

#### Minimum depth (155):

```cpp
    int minDepth(TreeNode *root) {
        // write your code here
        if(!root){
            return 0;
        }
        if(root->left && root->right) {
            return 1+min(minDepth(root->left),minDepth(root->right));
        } else if(root->left){
            return 1+ minDepth(root->left);
        } else if(root->right){
            return 1+ minDepth(root->right);
        } else {
            return 1;
        }
    }
```

#### Diameter (1181):


```cpp
    int diameterOfBinaryTree(TreeNode *root) {
        // write your code here
        if(!root){
            return 0;
        }
        int diameter = depth(root->left)+depth(root->right);
        diameter = max(diameter, diameterOfBinaryTree(root->left));
        diameter = max(diameter, diameterOfBinaryTree(root->right));
        return diameter;
    }

    int depth(TreeNode *root){
        if(!root){
            return 0;
        }
        return 1+max(depth(root->left),depth(root->right));
    }
```

### Binary Tree Paths (480):

```cpp
     vector<string> binaryTreePaths(TreeNode *root) {
        // write your code here
        vector<string> result;
        list<int> currPath;
        binaryTreePaths(root, result, currPath);
        return result;
    }

    void binaryTreePaths(TreeNode *head, vector<string> &result, list<int> &currPath){
        if(!head){
            return;
        }
        if(!head->left && !head->right){
            // currPath to string, including current leaf node
            string str = "";
            for(const auto &elem : currPath){
                str += convertIntToString((long int)elem)+"->";
            }
            str += convertIntToString(head->val);
            result.push_back(str);
            return;
        }
        currPath.push_back(head->val);
        binaryTreePaths(head->left, result, currPath);
        binaryTreePaths(head->right, result, currPath);
        currPath.pop_back();
    }

    string convertIntToString(long int value){
        bool negSign = false;
        if(value<0){
            negSign = true;
            value = -value;
        }
        string str = "";
        while(value>0){
            int rem = value%10;
            str = (char)('0'+rem) + str;
            value = value/10;
        }
        if(negSign){
            return "-"+str;
        }
        return str;
    }
```


#### Sum of Two Binary Trees (1126):

```cpp
     TreeNode* mergeTrees(TreeNode *t1, TreeNode *t2) {
        // Write your code here
        if(!t1 && !t2){
            return NULL;
        }
        int nodeVal = 0;
        if(t1){
            nodeVal += t1->val;
        }
        if(t2){
            nodeVal += t2->val;
        }
        TreeNode* node = new TreeNode(nodeVal);
        node->left = mergeTrees(t1?t1->left:NULL, t2?t2->left:NULL);
        node->right = mergeTrees(t1?t1->right:NULL, t2?t2->right:NULL);
        return node;
    }
```


### Longest Consecutive Sequence with Parent-child relation (595):

```cpp
     int longestConsecutive(TreeNode *root) {
        // write your code here
        int maxVal = 0;
        longestConsecutive(root, maxVal);
        return maxVal;
    }

    int longestConsecutive(TreeNode *head, int &maxOccur){
        if(!head){
            return 0;
        }
        int leftVal = longestConsecutive(head->left, maxOccur);
        int rightVal = longestConsecutive(head->right, maxOccur);
        maxOccur = max(maxOccur, leftVal);
        maxOccur = max(maxOccur, rightVal);
        int val = 1;
        if(head->left && head->val == head->left->val-1){
            val = max(val, 1+leftVal);
        }
        if(head->right && head->val == head->right->val-1){
            val = max(val, 1+rightVal);
        }
        maxOccur = max(maxOccur, val);
        return val;
    }
```



### Convert BST to Greater Tree (661):

Given a Binary Search Tree (BST), convert it to a Greater Tree such that every key of the original BST is changed to the original key plus sum of all keys greater than the original key in BST.

```cpp
    TreeNode* convertBST(TreeNode *root) {
        // write your code here
        if(!root){
            return NULL;
        }
        modifyBST(root, 0);
        return root;
    }

    int modifyBST(TreeNode *head, int increase){
        if(!head){
            return 0;
        }
        int rightSum = modifyBST(head->right, increase);
        int leftSum = modifyBST(head->left, head->val+rightSum+increase);
        int sum = leftSum + rightSum + head->val;
        head->val = head->val + rightSum + increase;
        return sum;
    }
```


### Second Minimum Node:

```cpp
    int findSecondMinimumValue(TreeNode *root) {
        // Write your code here
        int distinctValuesVisited = 0, firstValue=-1, secondValue=-1;
        secondMinimumValue(root, distinctValuesVisited, firstValue, secondValue);
        return secondValue;
    }

    void secondMinimumValue(TreeNode *head, int &distinctValuesVisited, int &firstValue, int &secondValue){
        if(!head){
            return;
        }
        if(distinctValuesVisited==0){
            firstValue = head->val;
            distinctValuesVisited = 1;
        } else if(distinctValuesVisited==1){
            if(head->val==firstValue){
                //continue
            } else{
                secondValue = head->val;
                distinctValuesVisited = 2;
                if(firstValue > secondValue){
                    int temp = firstValue;
                    firstValue = secondValue;
                    secondValue = temp;
                }
                // return;
            }
        } else {
            int temp = head->val;
            if(temp < firstValue){
                secondValue = firstValue;
                firstValue = temp;
            } else if(temp!=firstValue && temp < secondValue){
                secondValue = temp;
            }
        }
        secondMinimumValue(head->left, distinctValuesVisited,firstValue,secondValue);
        secondMinimumValue(head->right, distinctValuesVisited,firstValue,secondValue);
    }
```
