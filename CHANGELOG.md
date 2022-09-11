# Release Notes

## [1.0.0](https://github.com/cpcloud/protoletariat/compare/v0.9.4...1.0.0) (2022-09-11)


### ⚠ BREAKING CHANGES

* **deps:** Move to Python 3.8. 0.9.4 is the last version to support Python 3.7

* **deps:** bump python lower bound to 3.8 ([0480117](https://github.com/cpcloud/protoletariat/commit/04801176b74747199adcfe101f65c7c880662f07))

## [0.9.4](https://github.com/cpcloud/protoletariat/compare/v0.9.3...v0.9.4) (2022-06-22)


### Bug Fixes

* **codegen:** deduplicate generated imports ([e040217](https://github.com/cpcloud/protoletariat/commit/e040217ea9007e01f657cfb4ffcba80a9c8be23f))
* **codegen:** don't traverse or generate code with `__pycache__` ([0c083d5](https://github.com/cpcloud/protoletariat/commit/0c083d519442fd45bdb43328006818cd5e975df1))

### [0.9.3](https://github.com/cpcloud/protoletariat/compare/v0.9.2...v0.9.3) (2022-05-06)


### Bug Fixes

* fix version number again ([2865ce4](https://github.com/cpcloud/protoletariat/commit/2865ce40b83c4ecdf9132c457bd4992474af0b53))
* fix version number in `__init__.py` ([4fac8c8](https://github.com/cpcloud/protoletariat/commit/4fac8c893405e40db9d78758fcb89e20ed77395e))

### [0.9.2](https://github.com/cpcloud/protoletariat/compare/v0.9.1...v0.9.2) (2022-05-06)


### Bug Fixes

* fix version number in `__init__.py` ([fc494c9](https://github.com/cpcloud/protoletariat/commit/fc494c98f6b02ce460fee04c2774e5383cfffaa1))

### [0.9.1](https://github.com/cpcloud/protoletariat/compare/v0.9.0...v0.9.1) (2022-04-16)


### Bug Fixes

* replace hyphens with suffixes when cleaning proto filename ([71b9f27](https://github.com/cpcloud/protoletariat/commit/71b9f274b206a4096549acf94d9b9c4d01cd93e2))

# [0.9.0](https://github.com/cpcloud/protoletariat/compare/v0.8.0...v0.9.0) (2022-04-04)


### Features

* generate __init__.pyi for mypy ([9d7fe5b](https://github.com/cpcloud/protoletariat/commit/9d7fe5be7ace688e5e469fb474840e53f0f877ad))

# [0.8.0](https://github.com/cpcloud/protoletariat/compare/v0.7.5...v0.8.0) (2022-04-02)


### Features

* **buf:** pass input argument through to buf ([aacae63](https://github.com/cpcloud/protoletariat/commit/aacae63c14f71856157b8359abd0316d3a61608f))

## [0.7.5](https://github.com/cpcloud/protoletariat/compare/v0.7.4...v0.7.5) (2022-02-07)


### Bug Fixes

* add more underscores for imports ([ff4ca73](https://github.com/cpcloud/protoletariat/commit/ff4ca73fb9eafee247d3a4452085eee5cb188107))

## [0.7.4](https://github.com/cpcloud/protoletariat/compare/v0.7.3...v0.7.4) (2022-01-28)


### Performance Improvements

* build docker image with musl ([8c21eb5](https://github.com/cpcloud/protoletariat/commit/8c21eb58a80bce375509e1bddcef9aad2741cdcb))

## [0.7.3](https://github.com/cpcloud/protoletariat/compare/v0.7.2...v0.7.3) (2022-01-04)


### Bug Fixes

* fix release token to ensure publishing ([a97e98e](https://github.com/cpcloud/protoletariat/commit/a97e98e8e109c9ab65837ddf445a417e64284cb3))

## [0.7.2](https://github.com/cpcloud/protoletariat/compare/v0.7.1...v0.7.2) (2022-01-04)


### Bug Fixes

* move to upstream semantic-release ([b742a01](https://github.com/cpcloud/protoletariat/commit/b742a01857ef59085856a331ff77fb6bcdab5dd9))

## v0.7.1 (2021-12-24)
### Documentation
* Add some info ([`b4c9663`](https://github.com/cpcloud/protoletariat/commit/b4c96636efc65e2b21de7c3d2c4a68535afcdef9))
* Move the conda bit down ([`0cf67c4`](https://github.com/cpcloud/protoletariat/commit/0cf67c4321e52bbe0cc05bdf87c3c8d0b5fa074c))

### Performance
* Reduce everything up to but not including musl ([`c21a2a9`](https://github.com/cpcloud/protoletariat/commit/c21a2a9dd6de4be9353e2e704d643e2ac978d4de))

## v0.7.0 (2021-12-12)
### Feature
* Support click 7 ([`b994dad`](https://github.com/cpcloud/protoletariat/commit/b994dad32f0e4a66f20793f1526638a296004186))

### Documentation
* Link to protobuf issue ([`2b60855`](https://github.com/cpcloud/protoletariat/commit/2b608550bd85e9152189f4bf63806e543f383d45))

## v0.6.2 (2021-12-04)
### Fix
* Ensure every path is decoded as utf-8 ([`a936f08`](https://github.com/cpcloud/protoletariat/commit/a936f088884b94d91af88d2554f5dce1b5e37408))

## v0.6.1 (2021-12-02)
### Documentation
* Add some more information to the README.md ([`1d93380`](https://github.com/cpcloud/protoletariat/commit/1d93380ee9efc8159da96dd7600f95b5b6b83ec9))

### Performance
* Remove the use of a dict to store rewriters ([`72a8fd3`](https://github.com/cpcloud/protoletariat/commit/72a8fd367c11d951f1132f5b7e69ca4e7218807c))

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
