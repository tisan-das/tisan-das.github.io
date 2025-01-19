---
layout: post
title: Binary Search Problem Sets Part I
published: true
---

This wiki contains a couple of well-defined problems solved via Binary Search algorithm.

### Search for a Range (61):

```cpp
    int binSearch(vector<int> &array, int start, int end, int target){
        while(start <= end){
            int mid = (start+end)/2;
            if(array[mid] == target){
                return mid;
            } else if(array[mid] < target){
                start = mid+1;
            } else {
                end = mid-1;
            }
        }
        return -1;
    }


    int binSearchStart(vector<int> &array, int start, int end, int target){
        while(start <= end){
            if(start==end && array[start]==target){
                return start;
            } else if(start==end-1 && array[start]==target){
                return start;
            } else if(start==end-1 && array[end]==target){
                return end;
            } else if(start==end || start==end-1){
                return -1;
            }

            int mid = (start+end)/2;
            if(array[mid] == target){
                end = mid;
            } else if(array[mid] < target){
                start = mid+1;
            } else {
                end = mid-1;
            }
        }
        return -1;
    }

    int binSearchEnd(vector<int> &array, int start, int end, int target){
        while(start <= end){
            if(start==end && array[end]==target){
                return end;
            } else if(start==end-1 && array[end]==target){
                return end;
            } else if(start==end-1 && array[start]==target){
                return start;
            } else if(start==end || start==end-1){
                return -1;
            }

            int mid = (start+end)/2;
            if(array[mid] == target){
                start = mid;
            } else if(array[mid] < target){
                start = mid+1;
            } else {
                end = mid-1;
            }
        }
        return -1;
    }

    vector<int> searchRange(vector<int> &a, int target) {
        // write your code here
        // int index = binSearch(a,0,a.size()-1,target);
        // if(index == -1){
        //     return {-1,-1};
        // }
        // int startIndex=index, endIndex=index;
        // while(startIndex>0 && a[startIndex-1]==target){
        //     startIndex--;
        // }
        // while(endIndex<a.size()-1 && a[endIndex+1]==target){
        //     endIndex++;
        // }
        // return {startIndex, endIndex};
        int startIndex = binSearchStart(a, 0, a.size()-1, target);
        int endIndex = binSearchEnd(a, 0, a.size()-1, target);
        return {startIndex, endIndex};
    }
```



### Search in Rotated Sorted Array (62):

```cpp
    int findRotatedIndex(vector<int> &array, int start, int end){
        if(array[start] <= array[end]){
            return start;
        }
        while(start <= end){
            if(start==end){
                return start;
            } if(start==end-1 && array[start]<=array[end]){
                return start;
            } else if(start==end || start==end-1){
                return end;
            }

            int mid = (start+end)/2;
            if(array[start] > array[mid]){
                end = mid;
            } else {
                start = mid;
            }
        }
        return -1;
    }

    int binSearch(vector<int> &array, int start, int end, int target){
        while(start <= end){
            int mid = (start+end)/2;
            if(array[mid] == target){
                return mid;
            } else if(array[mid] < target){
                start = mid+1;
            } else {
                end = mid-1;
            }
        }
        return -1;
    }

    int search(vector<int> &a, int target) {
        // write your code here
        if(a.size()==0){
            return -1;
        }
        int rotatedIndex = findRotatedIndex(a, 0, a.size()-1);
        // cout<<"r:"<<rotatedIndex<<endl;
        if(target > a[a.size()-1]){
            return binSearch(a, 0, rotatedIndex-1, target);
        } else {
            return binSearch(a, rotatedIndex, a.size()-1, target);
        }
    }
```



### First Bad Version (74):

```cpp
    int findBinSearch(long long int start, long long int end){
        // if(!SVNRepo::isBadVersion(end)){
        //     return end;
        // }
        while(start <= end){
            // cout<<"start:"<<start<<" end:"<<end<<endl;
            if(start==end){
                if(SVNRepo::isBadVersion(start)){
                    return start;
                }
                return -1;
            } else if(start==end-1){
                if(SVNRepo::isBadVersion(start)){
                    return start;
                } else if(SVNRepo::isBadVersion(end)){
                    return end;
                }
                return -1;
            }

            // if(!SVNRepo::isBadVersion(end)){
            //     return end;
            // }
            long long int mid = (start+end)/2;
            if(SVNRepo::isBadVersion(mid)){
                end = mid;
            } else {
                start = mid;
            }
        }
        return -1;
    }

    int findFirstBadVersion(int n) {
        // write your code 
        return findBinSearch(1, n);
    }
```



### Search in Rotated Sorted Array II (63):

```cpp
    int findRotatedIndex(vector<int> &array, int start, int end){
        while(start <= end){
            if(array[start] < array[end]){
                return start;
            } else if(start==end){
                return start;
            } else if(start == end-1){
                if(array[start] <= array[end]){
                    return start;
                }
                return end;
            } else if(array[start] == array[end]){
                start++;
                end--;
                continue;
            }

            int mid = (start+end)/2;
            if(array[start] == array[mid]){
                start = mid;
            } else if(array[start] < array[mid]){
                start = mid;
            } else {
                end = mid;
            }
        }

        return -1;
    }

    int binSearch(vector<int> &array,int start, int end, int target){
        while(start <= end){
            int mid = (start+end)/2;
            if(array[mid] == target){
                return mid;
            } else if(array[mid] < target){
                start = mid+1;
            } else {
                end = mid-1;
            }
        }
        return -1;
    }

    bool search(vector<int> &a, int target) {
        // write your code here
        int rotatedIndex = findRotatedIndex(a, 0, a.size()-1);\
        // cout<<"rotated index:"<<rotatedIndex<<endl;
        if(rotatedIndex== -1){
            return false;
        }
        if(target > a[a.size()-1]){
            int index = binSearch(a, 0, rotatedIndex-1, target);
            if (index==-1){
                return false;
            }
            return true;
        } else {
            int index = binSearch(a, rotatedIndex, a.size()-1, target);
            if(index== -1){
                return false;
            }
            return true;
        }
    }
```



### Count of Smaller Number (248):

```cpp
    int findLowestUpper(vector<int> &array, int target){
        int start=0, end=array.size()-1;
        if(array.size()==0){
            return 0;
        }
        if(array[array.size()-1]<target){
            return array.size();
        }
        while(start <= end){
            if(start==end){
                return start;
            } else if(start==end-1 && array[start]>=target){
                return start;
            } else if(start==end-1){
                return end;
            }

            int mid = (start+end)/2;
            if(array[mid] < target){
                start = mid+1;
            } else {
                end = mid;
            }
        }
        return 0;
    }

    vector<int> countOfSmallerNumber(vector<int> &a, vector<int> &queries) {
        // write your code here
        sort(a.begin(), a.end());
        vector<int> result;
        for(int i=0;i<queries.size();i++){
            int index = findLowestUpper(a, queries[i]);
            result.push_back(index);
        }
        return result;
    }
```



### Copy Books (437):

```cpp
    bool isPossibletoComplete(vector<int> &array, int persons, int time){
        int remTime = time;
        int remPersons = persons;
        for(int i=0;i<array.size();i++){
            while(remTime<array[i] && remPersons>0){
                remTime = time;
                remPersons--;
            }
            if(remTime<array[i] || remPersons<=0){
                return false;
            }
            remTime -= array[i];
        }
        return true;
    }

    int binSearchPossibleTime(vector<int> &array, int persons){
        int start=1, end=0;
        for(int i=0;i<array.size();i++){
            end += array[i];
        }
        // what if it's not possible even with the largest number?

        while(start <= end){
            if(start == end){
                return start;
            } else if(start==end-1){
                if(isPossibletoComplete(array, persons, start)){
                    return start;
                }
                return end;
            }
            int mid = (start+end)/2;
            if(isPossibletoComplete(array, persons, mid)){
                end = mid;
            } else {
                start = mid;
            }
        }
        return 0;// not possible
    }
    int copyBooks(vector<int> &pages, int k) {
        // write your code here
        // for(int i=0;i<=10;i++){
        //     cout<<"i:"<<i<<", "<<isPossibletoComplete(pages,k,i)<<endl;
        // }
        return binSearchPossibleTime(pages, k);
    }
```



### How Many Problem Can I Accept (937):

```cpp
    long long canAccept(long long n, int k) {
        // Write your code here
        long long int value = sqrt((2 * (long long int)n) / (long long int)k + 0.25 ) - 0.5;
        return value;
    }
```



### Missing Element in Sorted Array (3661):

```cpp
    int binSearchLowerBoundDiff(vector<int> &array, int diffIndex){
        int start=0, end=array.size()-1;
        if(array.size()==0){
            return -1;
        }
        if(array[(array.size()-1)]-(array.size()-1)-array[0] < diffIndex){
            return array.size()-1;
        }
        while(start <= end){
            if(start==end){
                return start;
            } else if(start == end-1){
                if(array[end]-end-array[0] < diffIndex){
                    return end;
                }
                return start;
            }

            int mid = (start+end)/2;
            if(array[mid]-mid-array[0] < diffIndex){
                start = mid;
            } else {
                end = mid;
            }
        }
        return -1;// only in trivial case
    }

    int missingElement(vector<int> &nums, int k) {
        // write your code here
        // cout<<"k:"<<k<<endl;
        // for(int i=0;i<nums.size();i++){
        //     cout<<nums[i]<<",";
        // }
        // cout<<endl;
        int index = binSearchLowerBoundDiff(nums, k);
        // cout<<"index:"<<index<<endl;
        if(index < 0){
            return k;
        }
        return nums[index]+(k-(nums[index]-nums[0]-index));
    }
```



### Count Pairs in Two Arrays (3733):

```cpp
    int binSearchGreaterThan(vector<int> &array, int startIndex, int endIndex, int target){
        int start=startIndex, end=endIndex;
        while(start <= end){
            if(start==end){
                if(array[start] >= target){
                    return start;
                }
                return -1;
            } else if(start==end-1){
                if(array[start] >= target){
                    return start;
                } else if(array[end] >= target){
                    return end;
                } else {
                    return -1;
                }
            }
            int mid = (start+end)/2;
            if(array[mid] >= target){
                end = mid;
            } else {
                start = mid;
            }
        }
        return -1;
    }

    long long countPairs(vector<int> &nums1, vector<int> &nums2) {
        // write your code here
        vector<int> array;
        for(int i=0;i<nums1.size();i++){
            array.push_back(nums1[i]-nums2[i]);
        }
        sort(array.begin(), array.end());
        
        // cout<<"sorted diff: ";
        // for(int i=0;i<array.size();i++){
        //     cout<<"("<<i<<":"<<array[i]<<") ";
        // }
        // cout<<endl;

        long long int count = 0;
        for(int i=0;i<array.size();i++){
            int targetVal = array[i]<0?(-array[i]+1):1;
            int index = binSearchGreaterThan(array, i+1, array.size()-1, targetVal);
            // cout<<"i:"<<i<<" targetVal:"<<targetVal<<" index:"<<index<<endl;
            if(index != -1){
                count += (array.size()-index);
            }
        }
        return count;
    }
```



### Single Element in a Sorted Array (1183):

```cpp
    int binSearchNonDuplicate(vector<int> &array){
        if(array.size()%2==0){
            return -1;
        }
        int start=0, end=array.size()-1;
        while(start <= end){
            if(start<=end && array[start]==array[start+1]){
                start++;
            }
            if(end<array.size()-1 && array[end]==array[end+1]){
                end++;
            }
            if(start==0){
                return start;
            }
            if(start>0 && array[start]!=array[start-1]){
                return start;
            }
            if(end>0 && array[end]!=array[end-1]){
                return end;
            }

            if(start==end){
                return start;
            } else if(start==end-1){
                if(start>0 && array[start]==array[start-1]){
                    return end;
                }
                return start;
            } else if(start==end-2){
                if(array[start]==array[start+1]){
                    return end;
                }
                return start;
            }

            int mid = (start+end)/2;
            // cout<<"start:"<<start<<" end:"<<end<<" mid:"<<mid<<endl;
            if(mid<array.size() && array[mid]==array[mid+1]){
                mid++;
            }
            // cout<<"start:"<<start<<" end:"<<end<<" mid2:"<<mid<<endl;
            if((start-mid)%2==0){
                start = mid;
            } else {
                end = mid;
            }
            // cout<<"start:"<<start<<" end:"<<end<<endl;
        }
        return -1;
    }
    int singleNonDuplicate(vector<int> &nums) {
        // write your code here
        int index = binSearchNonDuplicate(nums);
        // cout<<"index:"<<index<<endl;
        if(index>=0){
            return nums[index];
        }
        return -1;
    }
```



### Build a temple (1669):

```cpp
    bool isPossibleConstruct(int m, vector<int> &woods, int len){
        int remWoods = m;
        // cout<<"checking ispossible for val:"<<len<<" with sticks:"<<m<<endl;
        for(int i=0;i<woods.size();i++){
            remWoods -= woods[i]/len;
            // cout<<"i:"<<i<<" rem:"<<remWoods<<endl;
            if(remWoods <= 0){
                return true;
            }
        }
        return remWoods<=0?true:false;
    }

    int binSearch(int m, vector<int> &woods){
        int start=1, end=woods[woods.size()-1];
        while(start<=end){
            if(start==end){
                if(isPossibleConstruct(m, woods, start)){
                    return start;
                }
                return -1;
            } else if(start == end-1){
                if(isPossibleConstruct(m, woods, end)){
                    return end;
                }
                if(isPossibleConstruct(m, woods, start)){
                    return start;
                }
                return -1;
            }

            int mid = (start+end)/2;
            // cout<<"start:"<<start<<" end:"<<end<<" mid:"<<mid<<endl;
            if(!isPossibleConstruct(m, woods, mid)){
                end = mid;
            } else {
                start = mid;
            }
        }
        return -1;
    }

    int buildTemple(int m, vector<int> &woods) {
        // write your code here.
        sort(woods.begin(), woods.end());
        int len = binSearch(m, woods);
        return len;
    }
```



### Find Minimum in Rotated Sorted Array II (160):

```cpp
    int binSearchMinRotated(vector<int> &nums){
        int start=0, end=nums.size()-1;
        while(start <= end){
            if(start==end){
                return start;
            } else if(start==end-1){
                if(nums[start] <= nums[end]){
                    return start;
                }
                return end;
            }
            if(nums[start] < nums[end]){
                return start;
            }
            int mid = (start+end)/2;
            // cout<<"start:"<<start<<" end:"<<end<<" mid:"<<mid<<endl;
            if(nums[start]==nums[mid]){
                start++;
                // end--;
            } else if(nums[end]==nums[mid]){
                end--;
            } else if(nums[start] > nums[mid]){
                end = mid;
            } else {
                start = mid; 
            }
        }
        return -1;
    }
    int findMin(vector<int> &nums) {
        // write your code here
        int index = binSearchMinRotated(nums);
        if(index >= 0){
            return nums[index];
        }
        return -1;
    }
```



### Kth Smallest Subarray Sum (3736):

```cpp
    int kthSmallestSubarraySum(vector<int> &nums, int k) {
        // write your code here

        priority_queue<int, vector<int>> heap;
        for(int i=0;i<nums.size();i++){
            int sum = 0;
            for(int j=i;j<nums.size();j++){
                sum += nums[j];
                heap.push(sum);
            }
        }

        while(heap.size()>k){
            // cout<<heap.top()<<",";
            heap.pop();
        }
        return heap.top();
    }
```



### Find K Closest Elements (460):

```cpp
    int binSearchUpperBoundIndex(vector<int> &array, int target){
        int start=0, end=array.size()-1;
        while(start <= end){
            if(start==end){
                return start;
            } else if(start==end-1){
                if(array[start] >= target){
                    return start;
                }
                return end;
            }

            int mid = (start+end)/2;
            // cout<<"start:"<<start<<" end:"<<end<<" mid:"<<mid<<endl;
            if(array[mid] == target){
                return mid;
            } else if(array[mid] < target){
                start = mid;
            } else {
                end = mid;
            }
        }
        return -1;
    }

    vector<int> kClosestNumbers(vector<int> &a, int target, int k) {
        // write your code here
        int index = binSearchUpperBoundIndex(a, target);
        vector<int> result;
        if(index == -1){
            return result;
        }
        // cout<<"index:"<<index<<endl;

        int i=index-1,j=i+1;
        for(int ii=0;ii<k;ii++){
            if(i<0 && j>=a.size()){
                break;
            } else if(i<0){
                result.push_back(a[j++]);
            } else if(j>=a.size()){
                result.push_back(a[i--]);
            } else if(abs(a[i]-target) <= abs(a[j]-target)){
                result.push_back(a[i--]);
            } else {
                result.push_back(a[j++]);
            }
        }
        return result;
    }
```



### H-Index II (1303):

```cpp
    int binSearch(vector<int> &citations){
        int start=0, end=citations.size()-1;
        while(start <= end){
            if(start == end){
                if(citations[start] >= citations.size()-start){
                    return start;
                }
                return -1;
            } else if(start == end-1){
                if(citations[start] >= citations.size()-start){
                    return start;
                }
                if(citations[end] >= citations.size()-end){
                    return end;
                }
                return -1;
            }

            int mid = start + (end-start)/2;
            // cout<<"start:"<<start<<" end:"<<end<<" mid:"<<mid<<endl;
            if(citations[mid] >= citations.size()-mid){
                end = mid;
            } else {
                start = mid;
            }
        }
        return -1;
    }

    int hIndex(vector<int> &citations) {
        // write your code here
        // sort(citations.begin(), citations.end());

        // Binary search to find the smallest index where citations[i] >= n - i
        int index = binSearch(citations);
        // cout<<"index:"<<index<<endl;
        if(index < 0){
            return 0;
        }
        return citations.size()-index;
    }
```



### Kth Smallest Number in Sorted Matrix (401):

```cpp
    int kthSmallest(vector<vector<int>> &matrix, int k) {
        // write your code here

        priority_queue<int, vector<int>> heap;
        for(int i=0;i<matrix.size();i++){
            if(i>=k){
                break;
            }
            for(int j=0;j<matrix[i].size();j++){
                if(j>=k){
                    break;
                }
                heap.push(matrix[i][j]);
                if(heap.size() > k){
                    heap.pop();
                }
            }
        }
        return heap.top();
    }
```



### Find Words (194):

```cpp
    bool isSubsequence(string &str, string &target){
        int tgtIndex = 0;
        for(int i=0;i<str.size();i++){
            if(tgtIndex<target.size() && target.at(tgtIndex)==str.at(i)){
                tgtIndex++;
            }
        }
        return tgtIndex==target.size();
    }

    vector<string> findWords(string &str, vector<string> &dict) {
        // write your code here.
        vector<string> result;
        for(string &tgt : dict){
            if(isSubsequence(str, tgt)){
                result.push_back(tgt);
            }
        }
        return result;
    }
```



