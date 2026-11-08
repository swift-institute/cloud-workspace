#!/usr/bin/env python3
"""Writes /home/user/tools/swift-format.json from institute's Institute.Source.Policy+swiftFormat.swift (the source gate's
configuration: its rules list and settings). A new container needs this before format-changed.py or apply-repairs.py."""
import json, os, re
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(root, "repos/swift-institute/institute/Sources/Institute Source Policy/Institute.Source.Policy+swiftFormat.swift")).read()
block = src.split("swiftFormatRules: [(Swift.String, Swift.Bool)] = [")[1].split("]")[0]
rules = {n: b == "true" for n, b in re.findall(r'\("(\w+)", (true|false)\)', block)}
conf = {"version": 1, "lineLength": 200, "indentation": {"spaces": 4}, "maximumBlankLines": 1, "respectsExistingLineBreaks": True,
        "lineBreakBeforeControlFlowKeywords": False, "lineBreakBeforeEachArgument": True, "lineBreakBeforeEachGenericRequirement": True,
        "prioritizeKeepingFunctionOutputTogether": True, "indentConditionalCompilationBlocks": True, "indentSwitchCaseLabels": False,
        "spacesAroundRangeFormationOperators": False, "fileScopedDeclarationPrivacy": {"accessLevel": "private"}, "rules": rules}
for k in ("lineLength", "maximumBlankLines"):  # fail loudly if the policy's literal settings changed
    assert f'("{k}", ' in src, k
os.makedirs("/home/user/tools/tmp", exist_ok=True)
json.dump(conf, open("/home/user/tools/swift-format.json", "w"), indent=2)
print(len(rules), "rules ->", "/home/user/tools/swift-format.json")
