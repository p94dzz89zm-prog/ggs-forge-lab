import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Pure-JDK subprocess contracts, including a deliberately discarding handler. */
public final class RegressionLauncherRegression {
    public static final class Arguments {
        public static void main(String[] args) {
            require(Arrays.equals(args, new String[] {"-1", "two words"}), "argument forwarding");
            System.out.println("CHILD_ARGUMENTS_OK");
        }
    }

    public static final class SilentAssertion {
        public static void main(String[] args) {
            Thread.setDefaultUncaughtExceptionHandler((thread, error) -> {});
            throw new AssertionError("original-deliberate-assertion");
        }
    }

    public static final class StaticFailure {
        static {
            if (System.nanoTime() != Long.MIN_VALUE) throw new IllegalStateException("original-static-failure");
        }
        public static void main(String[] args) {}
    }

    private record Result(int status, String output) {}

    private static Result run(String... args) throws Exception {
        List<String> command = new ArrayList<>(List.of(
            Path.of(System.getProperty("java.home"), "bin", "java").toString(),
            "-XX:-UsePerfData", "-cp", System.getProperty("java.class.path")));
        command.addAll(Arrays.asList(args));
        ProcessBuilder builder = new ProcessBuilder(command).redirectErrorStream(true);
        // These children test an exact stdout/traceback contract. Ambient JVM
        // options inject banners and unrelated agents before main executes.
        // Isolate only this fixture; production/suite launchers retain their
        // environment and never filter warning or failure text from logs.
        for (String key : List.of("JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS")) {
            builder.environment().remove(key);
        }
        Process process = builder.start();
        if (!process.waitFor(15, TimeUnit.SECONDS)) {
            process.destroyForcibly();
            throw new AssertionError("child process timed out");
        }
        return new Result(process.exitValue(), new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8));
    }

    private static void require(boolean condition, String reason) {
        if (!condition) throw new AssertionError(reason);
    }

    public static void main(String[] args) throws Exception {
        Result success = run("RegressionLauncher", Arguments.class.getName(), "-1", "two words");
        require(success.status == 0 && success.output.equals("CHILD_ARGUMENTS_OK\n"), "successful arguments");
        Result suppressed = run(SilentAssertion.class.getName());
        require(suppressed.status != 0 && suppressed.output.isEmpty(), "control must suppress original traceback");
        Result assertion = run("RegressionLauncher", SilentAssertion.class.getName());
        require(assertion.status == 1 && assertion.output.contains("java.lang.AssertionError: original-deliberate-assertion")
            && assertion.output.contains("SilentAssertion.main"), "original assertion traceback retained");
        Result initialization = run("RegressionLauncher", StaticFailure.class.getName());
        require(initialization.status == 1 && initialization.output.contains("ExceptionInInitializerError")
            && initialization.output.contains("original-static-failure"), "initialization cause retained");
        Result missing = run("RegressionLauncher", "RegressionLauncherMissingFixture");
        require(missing.status == 1 && missing.output.contains("ClassNotFoundException"), "missing suite fails visibly");
        Result empty = run("RegressionLauncher");
        require(empty.status == 2 && empty.output.contains("requires a suite class"), "missing suite argument fails");
        System.out.println("Checks passed: 6");
        System.exit(0);
    }
}
