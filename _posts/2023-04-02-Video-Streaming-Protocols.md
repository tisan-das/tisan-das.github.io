---
published: true
---
Video streaming has become one of the most popular forms of consuming content on the Internet. Because of this, even though the Internet was started as a method of transferring textual data, the audio-visual segment is currently responsible for the majority of Internet traffic. To handle such traffic efficiently different protocols for video streaming are developed. In this blog, we will learn about some video streaming protocols.

### Audio Concept:
Audio or sound is a natural phenomenon. The sound travels through a medium as the particles in the medium vibrate and the vibration of one particle causes the next particle also to vibrate, thus creating a wave through the medium. Like any kind of wave, the sound wave also can be thought of as a function of two parameters: the amplitude, which denotes how further the particle vibrates, and the frequency, which denotes how many times they vibrate in a time unit. Computers however being digital, need to convert this natural sound phenomenon in analog form to a digital signal using an A/D converter. The main principle here is sampling, where the audio is sampled at a periodic interval:
![](../images/video-streaming-protocols/audio-waveform-samples1.svg)

One of the main properties of sampling is the sample rate, which denotes the number of times the audio is sampled in a second. And each such sample denotes the amplitude of the signal at that specific time, each sample is stored using an integer or floating data type, and a stream of samples creates a channel. There can be multiple channels, for eg majority of the audio sources contain 2 sources: left and right; 5.1 type of another popular one, having a total of 6 channels.

The human ear operates on the frequency range of 20-20000 Hz, and based on the Nyquist-Shannon sampling theorem, the audio should be sampled at at-least 40kHz frequency to accurately recreate. Also having some more frequency bandwidth helps to avoid distortion, hence 44.1 kHz is the most popular sample rate. 

![](../images/video-streaming-protocols/audio-sample-bandwidth.png)

Thus based on the above calculation, 192KBps only for single audio is too huge and thus needs compression and decompression techniques(codec). It's to be noted that once codecs are used, we need to ensure the erroneous or dropped packets are recovered, otherwise the decompression might get failed. Due to this TCP connections are preferred over UDP ones for the majority of the codec.

### Video Concept:
The following calculation shows the massive requirement of bandwidth if the videos are transmitted uncompressed
![](../images/video-streaming-protocols/video-bandwidth.png)

Also, this is the same reason why lossy compression algorithms are preferred over lossless compression ones, at least for video media types.

The videos are generally encoded with either an RGB color system or a YUV color encoding system.

Recommended codec: 
- A WebM container using the VP9 codec for video and the Opus codec for audio
- An MP4 container and the AVC (H.264) video codec, ideally with AAC as your audio codec


### DASH:
DASH (Dynamic Adaptive Streaming over HTTP) is an adaptive bit-rate protocol, which supports video streaming through an HTTP web server. The video file is partitioned into multiple segments. Each segment contains a short interval playback time, and each partitioned content is available under different bit rates. The MPD file contains the information regarding all the segments, for all the partitioned segments for different bit-rates corresponding to the video, along with the segregated audio file. DASH supports live stream video as well. The DASH client uses an Adaptive Bit Rate (ABR) algorithm to select the segment with the highest bit rate and seamlessly adapts the resolution depending upon changing network behavior.

DASH uses two different profiles: A live profile for live streaming, and an On-demand profile for the rest of the videos. All these profiles have audio segregated and contain segments with different bit rates, and everything having stitched by the MPD file, and the HTML points to the MPD file, rather than pointing to individual video files.

```html
<video>
  <source src="my.mpd" type="application/dash+xml" />
  <!-- fallback -->
  <source src="my.mp4" type="video/mp4" />
  <source src="my.webm" type="video/webm" />
</video>
```
As different web servers provide support for DASH out-of-the-box, we would not go into details about how MPD files can be generated, rather we would explore the changes needed to be done on the web server side, to support DASH.

NGINX provides support for DASH through an external RTMP module. NGINX can be compiled with the RTMP module as follows: 
```sh
$ sudo apt install libpcre3-dev libssl-dev zlib1g-dev
$ sudo yum groupinstall pcre-devel zlib-devel openssl-devel


$ cd /path/to/build/dir
$ git clone https://github.com/arut/nginx-rtmp-module.git
$ git clone https://github.com/nginx/nginx.git
$ cd nginx
$ ./auto/configure --add-module=../nginx-rtmp-module
$ make
$ sudo make install

```

```conf
rtmp { 
    server { 
        listen 1935; 
        application live { 
            live on; 
            dash on; 
            dash_path /tmp/dash; 
            dash_fragment 15s; 
        } 
    } 
} 
 
http { 
    server { 
        listen 80; 
        location /tv { 
            root /tmp/dash; 
        } 
    }
 
    types {
        text/html html;
        application/dash+xml mpd;
    } 
}
```

### References:
1. [Digital Audio Concepts](https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Audio_concepts)
2. [Digital Video Concepts](https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Video_codecs)
3. [Web video codec guide](https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Video_codecs)
4. [DASH Adaptive Streaming for HTML 5 Video](https://developer.mozilla.org/en-US/docs/Web/Media/DASH_Adaptive_Streaming_for_HTML_5_Video)
5. [Setting up adaptive streaming media sources](https://developer.mozilla.org/en-US/docs/Web/Guide/Audio_and_video_delivery/Setting_up_adaptive_streaming_media_sources)
6. [Enabling Video Streaming for Remote Learning with NGINX and NGINX Plus](https://www.nginx.com/blog/video-streaming-for-remote-learning-with-nginx/)
7. [TCP Congestion Control](https://book.systemsapproach.org/congestion/tcpcc.html)
8. [NGINX Dash configuration](https://gist.github.com/shivasiddharth/30b998189c3dc76fdea4227f29e9dcf7)

