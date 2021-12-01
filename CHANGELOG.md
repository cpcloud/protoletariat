# Changelog

<!--next-version-placeholder-->

## v0.6.0 (2021-12-01)
### Feature
* Add the ability to bring your own (FileDescriptorSet) bytes ([`36589a6`](https://github.com/cpcloud/protoletariat/commit/36589a605585afde46ceec89bea790bff13c02fb))

### Documentation
* Update documentation ([`3a670a0`](https://github.com/cpcloud/protoletariat/commit/3a670a0624a92d41ec9a5c8039cba10c6eb10d09))

## v0.5.5 (2021-12-01)
### Documentation
* **README.md:** Remove redundant pypi badge ([`eca23d3`](https://github.com/cpcloud/protoletariat/commit/eca23d3b3ff8400cd73ed7951b88974c11a4e75a))
* Fix message about conda-forge artifacts ([`6b77fb2`](https://github.com/cpcloud/protoletariat/commit/6b77fb2676fded336a008314f7a3daea6713a155))
* Replace installation lines with table ([`8a1a702`](https://github.com/cpcloud/protoletariat/commit/8a1a7021fb2c5ab246319dad2a79451b06ba3426))
* Update README.md to include new options ([`ae2e8ea`](https://github.com/cpcloud/protoletariat/commit/ae2e8ea917475446f4f1ae6e52371b87ab387263))

### Performance
* Only iterate through files and dependencies once ([`561a616`](https://github.com/cpcloud/protoletariat/commit/561a616524cd9cd1f0107646635be60ef059b507))

## v0.5.4 (2021-11-29)
### Fix
* Add the ability to exclude google and optionally additional glob patterns from import rewrites ([`beadb73`](https://github.com/cpcloud/protoletariat/commit/beadb73227c03fc592f37f4bb7bd30b63188397c))

### Documentation
* Add docstring to _should_ignore ([`52225ad`](https://github.com/cpcloud/protoletariat/commit/52225ad2bcac4f7634cc86fe9e525da900a2d6b9))

## v0.5.3 (2021-11-29)
### Fix
* Don't require commitlint for release ([`1e1a7fe`](https://github.com/cpcloud/protoletariat/commit/1e1a7fe5fe36ffe2666c3d2b22490a2b46a68501))
* Split out buf tests to allow for skipping without a marker ([`b7dabca`](https://github.com/cpcloud/protoletariat/commit/b7dabca00d491b0f5bbac0bea830d5b50b38223c))
* Add buf marker to allow running tests if buf is known not be installable ([`50847d9`](https://github.com/cpcloud/protoletariat/commit/50847d93aba4e9bedb427265c8a18fb5556840c2))

## v0.5.2 (2021-11-28)
### Performance
* Use cpp implementation for python protobuf ([`ebc5614`](https://github.com/cpcloud/protoletariat/commit/ebc561447af11e2dfcef655695a7c4b5316cc92b))

## v0.5.1 (2021-11-28)
### Fix
* Use ast replacement everywhere because typed_ast/typed_astunparse performs correct roundtrip ([`627bffb`](https://github.com/cpcloud/protoletariat/commit/627bffb3512adae63bcd59dab6fce5cc2683f9a6))

### Documentation
* Add installation section to README.md ([`edd9dfc`](https://github.com/cpcloud/protoletariat/commit/edd9dfce36f9936fe46593713c12c0c258cb808a))
* Update README to include .pyi suffixes in help message ([`3e1ba1e`](https://github.com/cpcloud/protoletariat/commit/3e1ba1e6f1686e541ff211770b3f6a2aff28cbab))

## v0.5.0 (2021-11-26)
### Feature
* Add mypy and mypy grpc suffixes ([`e5a4b9e`](https://github.com/cpcloud/protoletariat/commit/e5a4b9e773c01926ebbd36d7316edb81b13810da))

### Fix
* Address imports in pyi that share a prefix ([`87a3f61`](https://github.com/cpcloud/protoletariat/commit/87a3f6151754db71106badca323ef59df782606a))
* Distinguish between single module imports versus froms in string replacements ([`8107d5a`](https://github.com/cpcloud/protoletariat/commit/8107d5abe16c5d0c8e1f68894935a33b81833737))

### Documentation
* Add comment about why the replacement strategies are necessary ([`f98e41c`](https://github.com/cpcloud/protoletariat/commit/f98e41c208f804627e81a7aba3a4b21708eaac5c))
* Fix readme to reflect CLI ([`f5d264d`](https://github.com/cpcloud/protoletariat/commit/f5d264d1d99a68c5344d6d8561b58599b2dd9799))

## v0.4.0 (2021-11-25)
### Feature
* Introduce module suffixes to allow adjustment of grpc generated code ([`b0b644a`](https://github.com/cpcloud/protoletariat/commit/b0b644a8daaa93850e4723e9bcaf47811294bb40))

### Fix
* Rewrite using per-file rewriters ([`baa883c`](https://github.com/cpcloud/protoletariat/commit/baa883cabb330fc289679d087f370a18e5ec5d15))

## v0.3.1 (2021-11-24)
### Fix
* Generate packages in the output directory ([`a00cc06`](https://github.com/cpcloud/protoletariat/commit/a00cc0651ee4244500443aca9b561278783d0587))
* Fix package relative imports ([`ae75384`](https://github.com/cpcloud/protoletariat/commit/ae753840f201478b373d38670bd9ee570079b4dc))

### Documentation
* Put a link to the pypi package in the badge ([`2053313`](https://github.com/cpcloud/protoletariat/commit/2053313726948bee12b25268b0584b5e3dd5a98e))
* Use shields.io instead of fury.io ([`7ae2261`](https://github.com/cpcloud/protoletariat/commit/7ae22611406fc8a210c459c3cf7299091458b0ae))
* Add status badges for CI and PyPI ([`318ba9f`](https://github.com/cpcloud/protoletariat/commit/318ba9f20c369c7a8b6161a5140b07b7787194f9))

## v0.3.0 (2021-11-24)
### Feature
* **cli:** Add support for generating FileDescriptorSet blobs using `buf` ([`2d072b7`](https://github.com/cpcloud/protoletariat/commit/2d072b7168521c33986a57a9b2f993522664f87b))

### Fix
* Remove warning from collections usage ([`7e0847e`](https://github.com/cpcloud/protoletariat/commit/7e0847e2fad40c198289ec564e4eaca895baf788))

### Documentation
* Fix typo in last "how it works" paragraph ([`3f8efde`](https://github.com/cpcloud/protoletariat/commit/3f8efde92bae74a59b641ecdcae8715e89418bbc))
* Update readme with CLI help changes ([`74b5648`](https://github.com/cpcloud/protoletariat/commit/74b5648e3f6a33d47cb0eea3e6e574fb95a9f55a))
* Fix typo ([`33a1505`](https://github.com/cpcloud/protoletariat/commit/33a15056eaff9e8b55f18fb30ad4ff0631bf9512))

## v0.2.1 (2021-11-23)
### Fix
* Fix docker image build ([`ffb262a`](https://github.com/cpcloud/protoletariat/commit/ffb262a905856b899747432530e026b0500dbf71))

### Documentation
* Fix typo ([`8a32b6b`](https://github.com/cpcloud/protoletariat/commit/8a32b6bc8d6a19e948e6475db28ec48b6b476f03))
* Describe how the thing works ([`bb05a58`](https://github.com/cpcloud/protoletariat/commit/bb05a589feff384f0b616166418b8309985b7567))
* More help ([`95b9f2a`](https://github.com/cpcloud/protoletariat/commit/95b9f2ac7f79494d3d8481b3b46c842f4f43f676))
* More readme ([`c57245b`](https://github.com/cpcloud/protoletariat/commit/c57245be0f842fe94e0a819b8d0c38a9d193ce78))

## v0.2.0 (2021-11-23)
### Feature
* Implement translation with rewrites ([`f7f05ce`](https://github.com/cpcloud/protoletariat/commit/f7f05cedd5f5bbaf8a85a1de7abbab7342ed2047))
* Initial environment setup ([`adafb9c`](https://github.com/cpcloud/protoletariat/commit/adafb9c8f4ca708e859814fb8ae8788fd5b023c2))

### Fix
* Remove 3.9-only with_stem method call ([`4d7f178`](https://github.com/cpcloud/protoletariat/commit/4d7f17875cb3fb909793bf3e7887f252a01ed5e7))
