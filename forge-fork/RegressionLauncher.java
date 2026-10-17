import java.lang.reflect.InvocationTargetException;
import java.util.Arrays;

/** Preserve suite failures before desktop uncaught handlers can consume them.
 * An explicit exit0 still requires the runner's exact completion marker.
 */
public final class RegressionLauncher {
    private RegressionLauncher() {}

    public static void main(String[] args) {
        if (args.length == 0) {
            System.err.println("RegressionLauncher requires a suite class and optional suite arguments");
            System.exit(2);
            return;
        }
        try {
            Class.forName(args[0]).getMethod("main", String[].class)
                .invoke(null, (Object) Arrays.copyOfRange(args, 1, args.length));
        } catch (Throwable failure) {
            Throwable original = failure instanceof InvocationTargetException && failure.getCause() != null
                ? failure.getCause() : failure;
            System.err.println("REGRESSION_LAUNCH_FAILURE suite=" + args[0]);
            original.printStackTrace(System.err);
            System.err.flush();
            System.exit(1);
        }
    }
}
