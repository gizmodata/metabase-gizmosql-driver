(defproject metabase-gizmosql-driver "1.0.1"
  :description "A Metabase driver for GizmoSQL — an Arrow Flight SQL server backed by DuckDB — using the GizmoSQL JDBC driver."
  :url "https://github.com/gizmodata/metabase-gizmosql-driver"
  :license {:name "Apache-2.0"
            :url "https://www.apache.org/licenses/LICENSE-2.0"}
  ;; Fixed name, so docker-compose.yaml doesn't break on every version bump.
  :uberjar-name "gizmosql.metabase-driver-standalone.jar"
  :dependencies [[org.clojure/clojure "1.12.3"]
                 [com.gizmodata/gizmosql-jdbc-driver "1.7.0"]]
  :repl-options {:init-ns metabase.driver.gizmosql})
