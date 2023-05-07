---
published: false
---
With the rapid adaption of microservice architectural pattern, one of the main issue has arised with secret management. With the microservices pattern, teams have become quite independent, and they interact through a well-defined endpoints, and apart from the API contract, the service is treated as black-box by the downstream services. As each team becomes indepdent, the independent nature is also reflected in all the aspects: starting from selecting tech-stack to design patterns used. And thus it increases the complexity in following core-security principle. And one major concern regarding this is leaking of security credentials. Storing security credentials on the codebase or setting them as environment variables from deployment pipeline, even though seems to enable quick implementation of features, however should be highly discouraged. To solve this kind of credential sprawling, enterprise level centralized credential management system is needed, and Hashicorp provides one such solution with Hashicorp Vault.

// Image of overview

### Vault Workflow
// Image of workflow

### Vault Secrets

### Vault Seal/Unseal
All the data stored in the vault is encrypted with encryption keys. And the vault needs access to the encryption key to decrypt the data. The encryption key is stored along with data, in a keyring. The encryption key is also 

### Vault policies


### References:
1. https://developer.hashicorp.com/vault/docs/what-is-vault
2. https://developer.hashicorp.com/vault/docs/concepts/seal


Enter text in [Markdown](http://daringfireball.net/projects/markdown/). Use the toolbar above, or click the **?** button for formatting help.
