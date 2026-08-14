import com.sun.source.tree.ClassTree;
import com.sun.source.tree.CompilationUnitTree;
import com.sun.source.tree.IfTree;
import com.sun.source.tree.MethodInvocationTree;
import com.sun.source.tree.MethodTree;
import com.sun.source.tree.ReturnTree;
import com.sun.source.tree.ThrowTree;
import com.sun.source.tree.Tree;
import com.sun.source.util.JavacTask;
import com.sun.source.util.SourcePositions;
import com.sun.source.util.TreePathScanner;
import com.sun.source.util.Trees;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;

public final class JavacAstOracle {
    private record AstRecord(String kind, long start, long end) {}

    private JavacAstOracle() {}

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("expected one Java source path");
        }
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) {
            throw new IllegalStateException("JDK compiler is unavailable");
        }
        Path source = Path.of(args[0]).toAbsolutePath().normalize();
        try (StandardJavaFileManager files = compiler.getStandardFileManager(null, null, null)) {
            Iterable<? extends JavaFileObject> units = files.getJavaFileObjects(source);
            JavacTask task = (JavacTask) compiler.getTask(
                    null, files, null, List.of("-proc:none", "--release", "17"), null, units);
            Iterable<? extends CompilationUnitTree> parsed = task.parse();
            Trees trees = Trees.instance(task);
            SourcePositions positions = trees.getSourcePositions();
            List<AstRecord> records = new ArrayList<>();
            for (CompilationUnitTree unit : parsed) {
                String sourceText = unit.getSourceFile().getCharContent(true).toString();
                new TreePathScanner<Void, Void>() {
                    private long byteOffset(long charOffset) {
                        if (charOffset < 0 || charOffset > sourceText.length()) {
                            throw new IllegalStateException("javac returned an invalid character offset");
                        }
                        return sourceText.substring(0, (int) charOffset)
                                .getBytes(StandardCharsets.UTF_8).length;
                    }

                    private void add(String kind, Tree tree) {
                        long charStart = positions.getStartPosition(unit, tree);
                        long charEnd = positions.getEndPosition(unit, tree);
                        if (charStart < 0 || charEnd < charStart) {
                            throw new IllegalStateException("javac returned an invalid source range");
                        }
                        long start = byteOffset(charStart);
                        long end = byteOffset(charEnd);
                        records.add(new AstRecord(kind, start, end));
                    }

                    @Override
                    public Void visitClass(ClassTree tree, Void unused) {
                        add("CLASS", tree);
                        return super.visitClass(tree, unused);
                    }

                    @Override
                    public Void visitMethod(MethodTree tree, Void unused) {
                        if (tree.getReturnType() != null) {
                            add("METHOD", tree);
                        }
                        return super.visitMethod(tree, unused);
                    }

                    @Override
                    public Void visitIf(IfTree tree, Void unused) {
                        add("IF", tree);
                        return super.visitIf(tree, unused);
                    }

                    @Override
                    public Void visitMethodInvocation(MethodInvocationTree tree, Void unused) {
                        add("METHOD_INVOCATION", tree);
                        return super.visitMethodInvocation(tree, unused);
                    }

                    @Override
                    public Void visitReturn(ReturnTree tree, Void unused) {
                        add("RETURN", tree);
                        return super.visitReturn(tree, unused);
                    }

                    @Override
                    public Void visitThrow(ThrowTree tree, Void unused) {
                        add("THROW", tree);
                        return super.visitThrow(tree, unused);
                    }
                }.scan(unit, null);
            }
            records.sort(Comparator.comparingLong(AstRecord::start)
                    .thenComparingLong(AstRecord::end)
                    .thenComparing(AstRecord::kind));
            for (AstRecord record : records) {
                System.out.printf("%s\t%d\t%d%n", record.kind(), record.start(), record.end());
            }
        }
    }
}
