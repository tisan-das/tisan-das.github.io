---
layout: post
title: Binary Search Problem Sets Part II
published: true
---

This wiki contains a couple of well-defined problems solved via Binary Search algorithm.



### Median of two Sorted Arrays (65):

```cpp
    double findMedian(vector<int> &a, vector<int> &b){
        double medianVal = 0;
        int i=0,j=0,k=0; 
        // 0 1 2 3 4 5 6 =>7, 0 1 2 3 4 5 =>6
        
        while( i<= ((a.size()+b.size()-1)/2) +1 ){
            // cout<<"checking i:"<<i<<" j:"<<j<<" k:"<<k<<endl;    
            int currVal = 0;
            if(j<a.size() && k<b.size()){
                if(a[j] <= b[k]){
                    currVal = a[j];
                    j++;
                } else {
                    currVal = b[k];
                    k++;
                }
            } else if(j<a.size()){
                currVal = a[j];
                j++;
            } else {
                currVal = b[k];
                k++;
            }
            // cout<<"currval at index "<<i<<":"<<currVal<<endl;

            if(i >= (a.size()+b.size()-1)/2 ){
                medianVal += currVal;
                // cout<<"med val :"<<medianVal<<","<<currVal<<endl;
                if((a.size()+b.size())%2==1){
                    break;
                }
            }
            i++;
        }
        return (a.size()+b.size())%2==1?medianVal:medianVal/2;
    }

    double findMedianSortedArrays(vector<int> &a, vector<int> &b) {
        // write your code here
        return findMedian(a,b);
    }
```



### Wood Cut (183):

```cpp
    bool isPossible(vector<int> &vec, int len, int pieces){
        int piecesLeft = pieces;
        for(int i=0;i<vec.size();i++){
            if(piecesLeft<=0){
                break;
            }
            piecesLeft -= (int)(vec[i]/len);
        }
        return piecesLeft<=0;
    }

    int binSearchPieces(vector<int> &vec, int pieces){
        
        int maxVal = 0;
        for(int i=0;i<vec.size();i++){
            maxVal = max(maxVal, vec[i]);
        }

        int low=1, high=maxVal;
        if(!isPossible(vec, 1, pieces)){
            return 0; // should it be 0??
        }
        while(low < high){
            if(low==high-1){
                if(isPossible(vec, high, pieces)){
                    return high;
                } else {
                    return low;
                }
            }
            int mid = low + (high-low)/2;
            if(isPossible(vec, mid, pieces)){
                low = mid;
            } else {
                high = mid-1;
            }
        }
        return low;
    }

    int woodCut(vector<int> &l, int k) {
        // write your code here
        if(l.size()==0){
            return 0;
        }
        return binSearchPieces(l,k);
    }
```



### Minimize Max Distance to Gas Station (848):

```cpp
    bool isPossible(vector<int> &stations, int maxStations, double distance){
        int count = 0;
        // there's no entry for single station
        // cout<<"dist:"<<distance<<endl;
        for(int i=1;i<stations.size();i++){
            count += ((double)stations[i]-stations[i-1])/distance;
            if (count>maxStations){
                return false;
            }
        }
        // cout<<"count:"<<count<<endl;
        return count<=maxStations;
    }

    double findMinimizedDistance(vector<int> &stations, int maxStation){
        double low=0, high=stations[stations.size()-1];
        while(low < high-0.00001){
            double mid = low+(high-low)/2;
            // cout<<"l:"<<low<<" h:"<<high<<" m:"<<mid<<endl;
            if(isPossible(stations, maxStation, mid)){
                high = mid;
            } else {
                low = mid;
            }
        }
        // cout<<"l:"<<low<<" h:"<<high<<endl;
        return low;
    }

    double minmaxGasDist(vector<int> &stations, int k) {
        // Write your code here

        sort(stations.begin(), stations.end());
        return findMinimizedDistance(stations,k);

        // Curious case: why the following wouldn't work??
        // int total_elements = 0; 
        // // priority_queue<long double, vector<long double>, less<long double>> maxHeap;
        // priority_queue<long double> maxHeap;
        // for(int i=1;i<stations.size();i++){
        //     maxHeap.push((long double)stations[i]-stations[i-1]);
        //     total_elements++;
        // }

        // for(int i=0;i<k;i++){
        //     long double top = maxHeap.top();
        //     maxHeap.pop();
        //     if(total_elements<=k+2){
        //         maxHeap.push((long double)top/2);
        //         maxHeap.push((long double)top/2);
        //         total_elements++;
        //     }
        // }

        // return maxHeap.top();
    }
```


