// Reads Swift files named on stdin (one path per line) and prints one JSON object per file:
// declarations with their shape, extensions with their members, imports, and the set of identifiers used.
import Foundation
import SwiftParser
import SwiftSyntax

func access(_ mods: DeclModifierListSyntax) -> String {
    for m in mods {
        switch m.name.tokenKind {
        case .keyword(.public): return "public"
        case .keyword(.open): return "open"
        case .keyword(.package): return "package"
        case .keyword(.internal): return "internal"
        case .keyword(.fileprivate): return "fileprivate"
        case .keyword(.private): return "private"
        default: continue
        }
    }
    return "default"
}

func trimmed(_ s: some SyntaxProtocol) -> String { s.trimmedDescription }

final class Visitor: SyntaxVisitor {
    let converter: SourceLocationConverter
    var scope: [String] = []
    var decls: [[String: Any]] = []
    var exts: [[String: Any]] = []
    var idents = Set<String>()
    var imports: [[String: Any]] = []
    var ifFalse = 0
    var availableDeprecated = 0
    init(_ tree: SourceFileSyntax, file: String) {
        converter = SourceLocationConverter(fileName: file, tree: tree)
        super.init(viewMode: .sourceAccurate)
    }
    func line(_ n: some SyntaxProtocol) -> Int { converter.location(for: n.positionAfterSkippingLeadingTrivia).line }

    override func visit(_ t: TokenSyntax) -> SyntaxVisitorContinueKind {
        if case .identifier(let s) = t.tokenKind { idents.insert(s) }
        return .visitChildren
    }
    override func visit(_ n: ImportDeclSyntax) -> SyntaxVisitorContinueKind {
        imports.append([
            "module": n.path.map { $0.name.text }.joined(separator: "."),
            "access": access(n.modifiers),
            "exported": n.attributes.contains { trimmed($0).hasPrefix("@_exported") },
            "line": line(n),
        ])
        return .skipChildren
    }
    override func visit(_ n: IfConfigClauseSyntax) -> SyntaxVisitorContinueKind {
        if let c = n.condition, trimmed(c) == "false" { ifFalse += 1 }
        return .visitChildren
    }
    override func visit(_ n: AttributeSyntax) -> SyntaxVisitorContinueKind {
        let s = trimmed(n)
        if s.hasPrefix("@available"), s.contains("deprecated") || s.contains("unavailable") || s.contains("obsoleted") { availableDeprecated += 1 }
        return .visitChildren
    }

    func members(_ block: MemberBlockSyntax) -> [String: Any] {
        var stored: [[String: String]] = []
        var computed = 0, funcs = 0, inits = 0, subscripts = 0, nested = 0, cases: [[String: Any]] = []
        var throwingOrFailableInit = false, customDecode = false, customEncode = false, staticLets = 0
        var memberNames: [String] = []
        for item in block.members {
            let d = item.decl
            if let v = d.as(VariableDeclSyntax.self) {
                let isStatic = v.modifiers.contains { $0.name.tokenKind == .keyword(.static) || $0.name.tokenKind == .keyword(.class) }
                for b in v.bindings {
                    let name = trimmed(b.pattern)
                    memberNames.append(name)
                    var isComputed = false
                    if let acc = b.accessorBlock {
                        switch acc.accessors {
                        case .getter: isComputed = true
                        case .accessors(let list):
                            isComputed = list.contains { a in
                                switch a.accessorSpecifier.tokenKind {
                                case .keyword(.get), .keyword(.set), .keyword(._read), .keyword(._modify), .keyword(.unsafeAddress), .keyword(.unsafeMutableAddress): return true
                                default: return false
                                }
                            } && !list.contains { $0.accessorSpecifier.tokenKind == .keyword(.willSet) || $0.accessorSpecifier.tokenKind == .keyword(.didSet) }
                        }
                    }
                    if isStatic { staticLets += 1; continue }
                    if isComputed { computed += 1 } else {
                        stored.append(["name": name, "type": b.typeAnnotation.map { trimmed($0.type) } ?? "?", "access": access(v.modifiers), "binding": v.bindingSpecifier.text])
                    }
                }
            } else if let f = d.as(FunctionDeclSyntax.self) {
                funcs += 1; memberNames.append(f.name.text)
                if f.name.text == "encode", trimmed(f.signature.parameterClause).hasPrefix("(to") { customEncode = true }
            } else if let i = d.as(InitializerDeclSyntax.self) {
                inits += 1
                let params = trimmed(i.signature.parameterClause)
                if params.hasPrefix("(from decoder") || params.hasPrefix("(from:") { customDecode = true }
                if i.optionalMark != nil || i.signature.effectSpecifiers?.throwsClause != nil { throwingOrFailableInit = true }
            } else if d.is(SubscriptDeclSyntax.self) { subscripts += 1 }
            else if let e = d.as(EnumCaseDeclSyntax.self) {
                for el in e.elements {
                    cases.append(["name": el.name.text, "payload": el.parameterClause?.parameters.count ?? 0, "payloadTypes": el.parameterClause.map { $0.parameters.map { trimmed($0.type) } } ?? []])
                }
            } else if d.is(StructDeclSyntax.self) || d.is(EnumDeclSyntax.self) || d.is(ClassDeclSyntax.self) || d.is(ActorDeclSyntax.self) || d.is(TypeAliasDeclSyntax.self) || d.is(ProtocolDeclSyntax.self) {
                nested += 1
            }
        }
        return ["stored": stored, "computed": computed, "funcs": funcs, "inits": inits, "subscripts": subscripts, "nested": nested,
                "cases": cases, "validatingInit": throwingOrFailableInit, "customDecode": customDecode, "customEncode": customEncode,
                "staticMembers": staticLets, "memberNames": memberNames]
    }

    func record(kind: String, name: String, mods: DeclModifierListSyntax, attrs: AttributeListSyntax, generics: GenericParameterClauseSyntax?, inherit: InheritanceClauseSyntax?, block: MemberBlockSyntax?, node: some SyntaxProtocol, extra: [String: Any] = [:]) {
        var d: [String: Any] = [
            "kind": kind, "name": name, "qualified": (scope + [name]).joined(separator: "."), "access": access(mods),
            "generic": generics != nil, "genericParams": generics.map { $0.parameters.map { $0.name.text } } ?? [],
            "inherits": inherit.map { $0.inheritedTypes.map { trimmed($0.type) } } ?? [],
            "attributes": attrs.map { trimmed($0) }.filter { $0.count < 120 },
            "line": line(node), "endLine": converter.location(for: node.endPositionBeforeTrailingTrivia).line, "nestedIn": scope.joined(separator: "."),
        ]
        if let block { d.merge(members(block)) { $1 } }
        d.merge(extra) { $1 }
        decls.append(d)
    }
    override func visit(_ n: StructDeclSyntax) -> SyntaxVisitorContinueKind {
        record(kind: "struct", name: n.name.text, mods: n.modifiers, attrs: n.attributes, generics: n.genericParameterClause, inherit: n.inheritanceClause, block: n.memberBlock, node: n)
        scope.append(n.name.text); return .visitChildren
    }
    override func visitPost(_ n: StructDeclSyntax) { scope.removeLast() }
    override func visit(_ n: EnumDeclSyntax) -> SyntaxVisitorContinueKind {
        record(kind: "enum", name: n.name.text, mods: n.modifiers, attrs: n.attributes, generics: n.genericParameterClause, inherit: n.inheritanceClause, block: n.memberBlock, node: n)
        scope.append(n.name.text); return .visitChildren
    }
    override func visitPost(_ n: EnumDeclSyntax) { scope.removeLast() }
    override func visit(_ n: ClassDeclSyntax) -> SyntaxVisitorContinueKind {
        record(kind: "class", name: n.name.text, mods: n.modifiers, attrs: n.attributes, generics: n.genericParameterClause, inherit: n.inheritanceClause, block: n.memberBlock, node: n)
        scope.append(n.name.text); return .visitChildren
    }
    override func visitPost(_ n: ClassDeclSyntax) { scope.removeLast() }
    override func visit(_ n: ActorDeclSyntax) -> SyntaxVisitorContinueKind {
        record(kind: "actor", name: n.name.text, mods: n.modifiers, attrs: n.attributes, generics: n.genericParameterClause, inherit: n.inheritanceClause, block: n.memberBlock, node: n)
        scope.append(n.name.text); return .visitChildren
    }
    override func visitPost(_ n: ActorDeclSyntax) { scope.removeLast() }
    override func visit(_ n: ProtocolDeclSyntax) -> SyntaxVisitorContinueKind {
        record(kind: "protocol", name: n.name.text, mods: n.modifiers, attrs: n.attributes, generics: nil, inherit: n.inheritanceClause, block: nil, node: n)
        scope.append(n.name.text); return .visitChildren
    }
    override func visitPost(_ n: ProtocolDeclSyntax) { scope.removeLast() }
    override func visit(_ n: TypeAliasDeclSyntax) -> SyntaxVisitorContinueKind {
        record(kind: "typealias", name: n.name.text, mods: n.modifiers, attrs: n.attributes, generics: n.genericParameterClause, inherit: nil, block: nil, node: n, extra: ["target": trimmed(n.initializer.value)])
        return .visitChildren
    }
    override func visit(_ n: ExtensionDeclSyntax) -> SyntaxVisitorContinueKind {
        let ext = trimmed(n.extendedType)
        var e: [String: Any] = ["extended": ext, "access": access(n.modifiers), "line": line(n), "endLine": converter.location(for: n.endPositionBeforeTrailingTrivia).line,
                                "inherits": n.inheritanceClause.map { $0.inheritedTypes.map { trimmed($0.type) } } ?? [],
                                "where": n.genericWhereClause.map { trimmed($0) } ?? ""]
        e.merge(members(n.memberBlock)) { $1 }
        exts.append(e)
        scope.append(ext); return .visitChildren
    }
    override func visitPost(_ n: ExtensionDeclSyntax) { scope.removeLast() }
}

var out = FileHandle.standardOutput
while let path = readLine() {
    guard let data = FileManager.default.contents(atPath: path), let text = String(data: data, encoding: .utf8) else { continue }
    let tree = Parser.parse(source: text)
    let v = Visitor(tree, file: path)
    v.walk(tree)
    let obj: [String: Any] = ["file": path, "lines": text.split(separator: "\n", omittingEmptySubsequences: false).count,
                              "decls": v.decls, "extensions": v.exts, "imports": v.imports, "idents": v.idents.sorted(),
                              "ifFalse": v.ifFalse, "availableDeprecated": v.availableDeprecated]
    let json = try JSONSerialization.data(withJSONObject: obj, options: [.sortedKeys])
    out.write(json); out.write(Data("\n".utf8))
}
