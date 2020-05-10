FROM quay.io/eduk8s/pkgs-java-tools:master as java-tools

FROM quay.io/eduk8s/workshop-dashboard:200509.6d82d3d

COPY --from=java-tools --chown=1001:0 /opt/jdk8 /opt/java

COPY --from=java-tools --chown=1001:0 /opt/gradle /opt/

COPY --from=java-tools --chown=1001:0 /opt/maven /opt/

COPY --from=java-tools --chown=1001:0 /opt/theia/plugins/. /opt/theia/plugins/

COPY --from=java-tools --chown=1001:0 /home/eduk8s/. /home/eduk8s/

ENV PATH=/opt/java/bin:/opt/gradle/bin:/opt/maven/bin:$PATH \
    JAVA_HOME=/opt/java \
    M2_HOME=/opt/maven