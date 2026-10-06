Shader "MonumentValley/GradientBackground"
{
    Properties
    {
        _TopColor ("Top Color", Color) = (0.34, 0.16, 0.58, 1)
        _BottomColor ("Bottom Color", Color) = (0.08, 0.05, 0.16, 1)
    }

    SubShader
    {
        Tags { "Queue" = "Background" "RenderType" = "Background" "IgnoreProjector" = "True" }
        Cull Off
        Lighting Off
        ZWrite Off
        ZTest LEqual

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            fixed4 _TopColor;
            fixed4 _BottomColor;

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float4 position : SV_POSITION;
                float2 uv : TEXCOORD0;
            };

            v2f vert(appdata input)
            {
                v2f output;
                output.position = UnityObjectToClipPos(input.vertex);
                output.uv = input.uv;
                return output;
            }

            fixed4 frag(v2f input) : SV_Target
            {
                return lerp(_BottomColor, _TopColor, saturate(input.uv.y));
            }
            ENDCG
        }
    }
}
