package uk.ac.ucl.cs.sec.chainspace;

import org.apache.http.HttpResponse;
import org.apache.http.StatusLine;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.BasicResponseHandler;
import org.apache.http.impl.client.HttpClientBuilder;
import org.json.JSONObject;

import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.lang.reflect.Array;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;


/**
 * Utils
 *
 * Some general purpose utilities.
 */
public class Utils {

    /**
     * hash
     * Compute the SHA-256 hash of the input string.
     *
     * @param input the string to hash
     * @return the input's SHA-256 digest
     * @throws NoSuchAlgorithmException This exception should never happens since the algorithm is hardcoded
     */
    static String hash(String input) throws NoSuchAlgorithmException {

        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        digest.update(input.getBytes());
        byte[] hash = digest.digest();

        return javax.xml.bind.DatatypeConverter.printHexBinary(hash).toLowerCase();
    }


    /**
     * verifyHash
     * Verify a hash image against a SHA-256 digest.
     *
     * @param object the hash image
     * @param hashedValue the digest
     * @return whether the digest matches the hash image
     * @throws NoSuchAlgorithmException This exception should never happens since the algorithm is hardcoded
     */
    static boolean verifyHash(String object, String hashedValue) throws NoSuchAlgorithmException {

        return hash(object).equals(hashedValue);

    }


    /**
     * concatenate
     * Concatenate two arrays.
     * @param a the first array
     * @param b the second array
     * @param <T> the type of the arrays
     * @return a new array with the content of a and b
     */
    static <T> T[] concatenate(T[] a, T[] b) {
        int aLen = a.length;
        int bLen = b.length;

        @SuppressWarnings("unchecked")
        T[] c = (T[]) Array.newInstance(a.getClass().getComponentType(), aLen+bLen);
        System.arraycopy(a, 0, c, 0, aLen);
        System.arraycopy(b, 0, c, aLen, bLen);

        return c;
    }

    /**
     * generateObjectID
     * Create an object ID from the object and the trasaction that created it.
     */
    public static String generateObjectID(String transactionID, String object, int idx) throws NoSuchAlgorithmException {
        JSONObject obj = new JSONObject(object);
        String prefix="";
        if(obj.has("location")){
            prefix = obj.getInt("location") + "_";
        }
        return prefix + Utils.hash(transactionID + "|" + Utils.hash(object) + "|" + idx);
    }



    /**
     * generateHead
     * Create a new head from a new transaction and the previous head.
     */
    static String generateHead(String oldHead, String transactionJson) throws NoSuchAlgorithmException {
        return Utils.hash(oldHead + "|" + transactionJson);
    }

    /**
     * generateHead
     * Create a new head from a new transaction (should be used only for the first transaction).
     */
    static String generateHead(String transactionJson) throws NoSuchAlgorithmException {
        return Utils.hash(transactionJson);
    }

    static String makePostRequest(String url, String postData) throws IOException {
        return makePostRequest(url, postData, false);
    }

    /**
     * makePostRequest
     * Make a simple post request.
     * @param url to url where to make the request
     * @param postData the post data representing a json string
     * @return the string response of the server
     * @throws IOException general IO exception, thrown if anything goes bad
     */
    static String makePostRequest(String url, String postData, boolean log) throws IOException {

        // prepare post request
        HttpClient httpClient = HttpClientBuilder.create().build();
        StringEntity postingString = new StringEntity(postData);
        HttpPost post = new HttpPost(url);
        post.setEntity(postingString);
        post.setHeader("Content-type", "application/json");

        if (log) {
            System.out.println("POST " + url + " HTTP/1.1");
            System.out.println(postData);
        }
        // execute
        HttpResponse response   = httpClient.execute(post);

        // return string response
        String responseBody = new BasicResponseHandler().handleResponse(response);

        if (log) {
            StatusLine s = response.getStatusLine();
            System.out.println(s.getProtocolVersion() + " " + s.getStatusCode() + " " + s.getReasonPhrase());
            System.out.println(responseBody);
        }
        return responseBody;

    }


    /**
     * printHeader
     * Nicely display a header to the console.
     * @param title the title to print to the console
     */
    static void printHeader(String title) {
        System.out.println("\n-----------------------------------------------------------------------------");
        System.out.println("\t" + title);
        System.out.println("-----------------------------------------------------------------------------");
    }

    /**
     * printStacktrace
     * Nicely print the exception's stack trace to the console.
     * @param e the exception from with to print the stack trace
     */
    static void printStacktrace(Exception e) {
        System.out.println();
        e.printStackTrace();
        System.out.println();
    }

    /**
     * printLine
     * Draw a simple line to the console.
     */
    static void printLine() {
        System.out.println("\n-----------------------------------------------------------------------------");
        System.out.println("\n");
    }

}
