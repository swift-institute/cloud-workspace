# #239 Linux lane: status

Plan: (1) re-pin swift-format in Institute.Source.Policy and adopt it through .github/.institute-ci-pin/.institute-ci-planner, with the concept rules wired into ci.yml and ceilings re-measured; (2) read CI on every Institute main, fix real failures and move colliding test suites; (3) test the seven private portable coenttb packages on Linux and close on coenttb/work#239.

Platform for everything proven here: Linux x86_64, Swift 6.4.2. Apple and Windows code is not compiled here.

## Steps

1. **Source gate re-pin: in progress.**
   - Cause confirmed: GitHub's xcode-27 image 20261104.0337 carries Xcode 27.2 build 27B52; the pin recorded 27B48.
   - `institute` 3a43c132b72118b045a4eeb002fcd2937e974414: swift-format digest 475d31f4…, toolchain 27B52; ISO 9945 Kernel File (POSIX) dropped from institute targets for File System, which broke institute's Windows build since 53a421e; bundle test master list; swift-format findings. `swift test` on Linux: all pass.
   - publish-planner run 42245057187 for 3a43c13 (planner + linter runner).
   - **Blocked for this session: adoption.** `swift-institute/.github` can't be attached here (repository names starting with `.` are refused), and `institute planner canary` needs Xcode. Adoption is a Mac step; the exact commands go here once the publish runs finish.
2. Concept rules in ci.yml: tokens wait for the runner from 3a43c13 (commit B).
3. CI read: 448 mains read at 15:15 UTC: 299 pass, 107 fail, 42 no checks. Failing checks: Quality · source 67 (63 the swift-format hash), Embedded 20, Windows 7, macOS 2, Linux release 2.
4. Suite-name collisions: 1,344 suite-bearing extension blocks in 169 repositories; not started.
5. Private portable packages: attached; not started.
